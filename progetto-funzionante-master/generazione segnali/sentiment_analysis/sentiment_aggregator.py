"""
Sentiment Aggregator
Combina news sentiment, social media sentiment e options flow per una view unificata
"""

import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from .news_sentiment import NewsProvider, NewsSentimentAnalyzer, InstrumentNewsSentiment
from .social_sentiment import SocialMediaAnalyzer, SocialPlatform, SocialSentiment
from .options_flow import OptionsFlowAnalyzer, FlowAnalysis, UnusualActivity

logger = logging.getLogger(__name__)

class MarketSentimentType(Enum):
    VERY_BEARISH = "VERY_BEARISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"
    BULLISH = "BULLISH"
    VERY_BULLISH = "VERY_BULLISH"

@dataclass
class MarketSentiment:
    """Sentiment aggregato per uno strumento"""
    instrument: str
    timestamp: datetime
    timeframe_minutes: int
    
    # Composite scores (-1.0 to 1.0)
    overall_sentiment_score: float
    confidence_level: float  # 0.0 to 1.0
    sentiment_type: MarketSentimentType
    
    # Component sentiments
    news_sentiment: Optional[InstrumentNewsSentiment]
    social_sentiments: Dict[SocialPlatform, SocialSentiment]
    options_flow: Optional[FlowAnalysis]
    
    # Weighted component scores
    news_weight: float
    social_weight: float
    options_weight: float
    
    # Key insights
    sentiment_drivers: List[str]  # Main factors driving sentiment
    risk_factors: List[str]       # Contrarian signals or risks
    conviction_factors: List[str] # High conviction signals
    
    # Momentum and trends
    sentiment_momentum: str       # "BUILDING", "FADING", "STABLE"
    sentiment_divergence: bool    # True if components disagree significantly
    
    # Trading implications
    directional_bias: str         # "BULLISH", "BEARISH", "NEUTRAL"
    conviction_strength: str      # "LOW", "MEDIUM", "HIGH"
    time_horizon: str            # "SHORT", "MEDIUM", "LONG"
    
    # Alerts and notifications
    unusual_activity_detected: bool
    unusual_activities: List[UnusualActivity]

class SentimentAggregator:
    """Main sentiment aggregator combining all sources"""
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        # Initialize all analyzers
        self.news_provider = NewsProvider()
        self.news_analyzer = NewsSentimentAnalyzer(self.news_provider)
        self.social_analyzer = SocialMediaAnalyzer()
        self.options_analyzer = OptionsFlowAnalyzer()
        
        # Caching
        self.cache = {}
        self.cache_timeout = timedelta(minutes=10)
        
        # Dynamic weighting parameters
        self.default_weights = {
            "news": 0.3,
            "social": 0.2,
            "options": 0.5  # Options flow gets highest weight
        }
        
        # Instrument-specific weight adjustments
        self.instrument_weight_adjustments = {
            # Indices have strong options flow
            "SPX500_USD": {"options": 0.6, "news": 0.3, "social": 0.1},
            "NAS100_USD": {"options": 0.6, "news": 0.3, "social": 0.1},
            "US30_USD": {"options": 0.6, "news": 0.3, "social": 0.1},
            
            # Forex has strong news component
            "EUR_USD": {"news": 0.5, "options": 0.3, "social": 0.2},
            "GBP_USD": {"news": 0.5, "options": 0.3, "social": 0.2},
            
            # Metals have strong social component
            "XAU_USD": {"news": 0.4, "social": 0.3, "options": 0.3},
            "XAG_USD": {"news": 0.4, "social": 0.3, "options": 0.3}
        }

    async def get_comprehensive_sentiment(self, instrument: str, hours_back: int = 6) -> MarketSentiment:
        """Get comprehensive sentiment analysis for instrument"""
        
        # Check cache
        cache_key = f"{instrument}_{hours_back}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]["data"]
        
        # Fetch all sentiment components in parallel
        tasks = [
            self._get_news_sentiment(instrument, hours_back),
            self._get_social_sentiment(instrument, hours_back),
            self._get_options_sentiment(instrument, hours_back)
        ]
        
        try:
            news_sentiment, social_sentiments, options_flow = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            if isinstance(news_sentiment, Exception):
                logger.error(f"News sentiment error: {news_sentiment}")
                news_sentiment = None
            
            if isinstance(social_sentiments, Exception):
                logger.error(f"Social sentiment error: {social_sentiments}")
                social_sentiments = {}
                
            if isinstance(options_flow, Exception):
                logger.error(f"Options flow error: {options_flow}")
                options_flow = None
            
            # Create comprehensive sentiment
            sentiment = await self._create_comprehensive_sentiment(
                instrument, hours_back, news_sentiment, social_sentiments, options_flow
            )
            
            # Cache result
            self.cache[cache_key] = {
                "data": sentiment,
                "timestamp": datetime.utcnow()
            }
            
            return sentiment
            
        except Exception as e:
            logger.error(f"Error getting comprehensive sentiment: {e}")
            # Return neutral sentiment on error
            return self._create_neutral_sentiment(instrument, hours_back)

    async def _get_news_sentiment(self, instrument: str, hours_back: int) -> Optional[InstrumentNewsSentiment]:
        """Get news sentiment component"""
        try:
            return await self.news_analyzer.get_instrument_sentiment(instrument, hours_back * 60)
        except Exception as e:
            logger.error(f"Error fetching news sentiment: {e}")
            return None

    async def _get_social_sentiment(self, instrument: str, hours_back: int) -> Dict[SocialPlatform, SocialSentiment]:
        """Get social sentiment component"""
        try:
            return await self.social_analyzer.get_aggregated_sentiment(instrument, hours_back)
        except Exception as e:
            logger.error(f"Error fetching social sentiment: {e}")
            return {}

    async def _get_options_sentiment(self, instrument: str, hours_back: int) -> Optional[FlowAnalysis]:
        """Get options flow component"""
        try:
            # Only analyze options flow for instruments that have options
            if self._has_options_market(instrument):
                return await self.options_analyzer.analyze_flow(instrument, hours_back)
            return None
        except Exception as e:
            logger.error(f"Error fetching options flow: {e}")
            return None

    def _has_options_market(self, instrument: str) -> bool:
        """Check if instrument has active options market"""
        options_instruments = [
            "SPX500_USD", "NAS100_USD", "US30_USD",  # Indices (via SPY, QQQ, DIA)
            "XAU_USD", "XAG_USD"  # Metals (via GLD, SLV)
        ]
        return instrument in options_instruments

    async def _create_comprehensive_sentiment(
        self, 
        instrument: str, 
        hours_back: int,
        news_sentiment: Optional[InstrumentNewsSentiment],
        social_sentiments: Dict[SocialPlatform, SocialSentiment],
        options_flow: Optional[FlowAnalysis]
    ) -> MarketSentiment:
        """Create comprehensive sentiment from all components"""
        
        # Get dynamic weights for this instrument
        weights = self._get_dynamic_weights(instrument, news_sentiment, social_sentiments, options_flow)
        
        # Calculate component scores
        news_score = news_sentiment.relevance_weighted_sentiment if news_sentiment else 0.0
        
        # Social sentiment (average across platforms weighted by engagement)
        social_score = 0.0
        if social_sentiments:
            total_engagement = sum(s.total_engagement for s in social_sentiments.values())
            if total_engagement > 0:
                social_score = sum(
                    s.engagement_weighted_sentiment * (s.total_engagement / total_engagement)
                    for s in social_sentiments.values()
                )
        
        # Options flow sentiment
        options_score = options_flow.sentiment_score if options_flow else 0.0
        
        # Calculate weighted overall sentiment
        overall_sentiment = (
            news_score * weights["news"] +
            social_score * weights["social"] +
            options_score * weights["options"]
        )
        
        # Calculate confidence level
        confidence = self._calculate_confidence_level(
            news_sentiment, social_sentiments, options_flow, weights
        )
        
        # Determine sentiment type
        sentiment_type = self._score_to_sentiment_type(overall_sentiment)
        
        # Analyze sentiment drivers and risks
        drivers, risks, conviction_factors = self._analyze_sentiment_factors(
            news_sentiment, social_sentiments, options_flow
        )
        
        # Determine momentum
        momentum = self._calculate_sentiment_momentum(
            news_sentiment, social_sentiments, options_flow
        )
        
        # Check for divergence
        divergence = self._check_sentiment_divergence(news_score, social_score, options_score)
        
        # Trading implications
        directional_bias, conviction_strength, time_horizon = self._determine_trading_implications(
            overall_sentiment, confidence, options_flow, news_sentiment
        )
        
        # Check for unusual activities
        unusual_activities = []
        if options_flow:
            try:
                activities = await self.options_analyzer.detect_unusual_activity([instrument])
                unusual_activities.extend(activities)
            except Exception as e:
                logger.error(f"Error detecting unusual activity: {e}")
        
        return MarketSentiment(
            instrument=instrument,
            timestamp=datetime.utcnow(),
            timeframe_minutes=hours_back * 60,
            overall_sentiment_score=overall_sentiment,
            confidence_level=confidence,
            sentiment_type=sentiment_type,
            news_sentiment=news_sentiment,
            social_sentiments=social_sentiments,
            options_flow=options_flow,
            news_weight=weights["news"],
            social_weight=weights["social"],
            options_weight=weights["options"],
            sentiment_drivers=drivers,
            risk_factors=risks,
            conviction_factors=conviction_factors,
            sentiment_momentum=momentum,
            sentiment_divergence=divergence,
            directional_bias=directional_bias,
            conviction_strength=conviction_strength,
            time_horizon=time_horizon,
            unusual_activity_detected=len(unusual_activities) > 0,
            unusual_activities=unusual_activities
        )

    def _get_dynamic_weights(
        self, 
        instrument: str,
        news_sentiment: Optional[InstrumentNewsSentiment],
        social_sentiments: Dict[SocialPlatform, SocialSentiment],
        options_flow: Optional[FlowAnalysis]
    ) -> Dict[str, float]:
        """Calculate dynamic weights based on data quality and instrument type"""
        
        # Start with instrument-specific weights
        base_weights = self.instrument_weight_adjustments.get(instrument, self.default_weights.copy())
        
        # Adjust based on data quality
        adjustments = {"news": 1.0, "social": 1.0, "options": 1.0}
        
        # News quality adjustment
        if news_sentiment:
            if news_sentiment.articles_count >= 5 and news_sentiment.timeframe_minutes >= 120:
                adjustments["news"] = 1.2  # High quality news data
            elif news_sentiment.articles_count <= 2:
                adjustments["news"] = 0.7  # Low quality news data
        else:
            adjustments["news"] = 0.0  # No news data
        
        # Social quality adjustment
        if social_sentiments:
            total_posts = sum(s.posts_count for s in social_sentiments.values())
            if total_posts >= 20:
                adjustments["social"] = 1.2
            elif total_posts <= 5:
                adjustments["social"] = 0.7
        else:
            adjustments["social"] = 0.0
        
        # Options quality adjustment
        if options_flow:
            if options_flow.total_premium_flow >= 100000:  # $100K+ premium
                adjustments["options"] = 1.3
            elif options_flow.total_premium_flow <= 10000:
                adjustments["options"] = 0.7
        else:
            adjustments["options"] = 0.0
        
        # Apply adjustments
        adjusted_weights = {
            key: base_weights[key] * adjustments[key]
            for key in base_weights
        }
        
        # Normalize weights to sum to 1.0
        total_weight = sum(adjusted_weights.values())
        if total_weight > 0:
            adjusted_weights = {key: weight / total_weight for key, weight in adjusted_weights.items()}
        else:
            # Fallback to equal weights if no data
            adjusted_weights = {"news": 0.33, "social": 0.33, "options": 0.34}
        
        return adjusted_weights

    def _calculate_confidence_level(
        self,
        news_sentiment: Optional[InstrumentNewsSentiment],
        social_sentiments: Dict[SocialPlatform, SocialSentiment],
        options_flow: Optional[FlowAnalysis],
        weights: Dict[str, float]
    ) -> float:
        """Calculate overall confidence level"""
        
        confidence_components = []
        
        # News confidence
        if news_sentiment and weights["news"] > 0:
            news_confidence = min(1.0, news_sentiment.articles_count / 10.0)  # Max confidence at 10+ articles
            confidence_components.append(news_confidence * weights["news"])
        
        # Social confidence
        if social_sentiments and weights["social"] > 0:
            total_posts = sum(s.posts_count for s in social_sentiments.values())
            social_confidence = min(1.0, total_posts / 50.0)  # Max confidence at 50+ posts
            confidence_components.append(social_confidence * weights["social"])
        
        # Options confidence
        if options_flow and weights["options"] > 0:
            options_confidence = options_flow.conviction_score
            confidence_components.append(options_confidence * weights["options"])
        
        # Average weighted confidence
        if confidence_components:
            return sum(confidence_components) / sum(weights.values())
        else:
            return 0.0

    def _score_to_sentiment_type(self, score: float) -> MarketSentimentType:
        """Convert numeric score to sentiment type"""
        if score >= 0.6:
            return MarketSentimentType.VERY_BULLISH
        elif score >= 0.2:
            return MarketSentimentType.BULLISH
        elif score <= -0.6:
            return MarketSentimentType.VERY_BEARISH
        elif score <= -0.2:
            return MarketSentimentType.BEARISH
        else:
            return MarketSentimentType.NEUTRAL

    def _analyze_sentiment_factors(
        self,
        news_sentiment: Optional[InstrumentNewsSentiment],
        social_sentiments: Dict[SocialPlatform, SocialSentiment],
        options_flow: Optional[FlowAnalysis]
    ) -> Tuple[List[str], List[str], List[str]]:
        """Analyze factors driving sentiment"""
        
        drivers = []
        risks = []
        conviction_factors = []
        
        # News factors
        if news_sentiment:
            if news_sentiment.articles_count >= 5:
                drivers.append(f"Strong news coverage ({news_sentiment.articles_count} articoli)")
            
            if news_sentiment.sentiment_trend == "IMPROVING":
                drivers.append("Sentiment news in miglioramento")
            elif news_sentiment.sentiment_trend == "DETERIORATING":
                risks.append("Sentiment news in peggioramento")
            
            if news_sentiment.top_keywords:
                drivers.append(f"Keywords chiave: {', '.join(news_sentiment.top_keywords[:3])}")
        
        # Social factors
        if social_sentiments:
            for platform, sentiment in social_sentiments.items():
                if sentiment.posts_count >= 20:
                    drivers.append(f"Alta attività {platform.value} ({sentiment.posts_count} posts)")
                
                if sentiment.sentiment_momentum == "BUILDING":
                    conviction_factors.append(f"Momentum {platform.value} in crescita")
                elif sentiment.sentiment_momentum == "FADING":
                    risks.append(f"Momentum {platform.value} in calo")
                
                if sentiment.influencer_sentiment != 0:
                    if abs(sentiment.influencer_sentiment) > 0.3:
                        conviction_factors.append(f"Influencer {platform.value} sentiment forte")
        
        # Options factors
        if options_flow:
            if options_flow.total_premium_flow >= 500000:
                conviction_factors.append(f"Flusso opzioni elevato (${options_flow.total_premium_flow/1000:.0f}K)")
            
            if options_flow.aggressive_flow_ratio >= 0.6:
                conviction_factors.append("Alta percentuale flussi aggressivi")
            
            if options_flow.institutional_bias != "NEUTRAL":
                drivers.append(f"Bias istituzionale: {options_flow.institutional_bias}")
            
            if options_flow.put_call_ratio >= 1.5:
                risks.append("Ratio Put/Call elevato (sentiment bearish)")
            elif options_flow.put_call_ratio <= 0.5:
                drivers.append("Ratio Put/Call basso (sentiment bullish)")
        
        return drivers[:5], risks[:3], conviction_factors[:3]  # Limit number of factors

    def _calculate_sentiment_momentum(
        self,
        news_sentiment: Optional[InstrumentNewsSentiment],
        social_sentiments: Dict[SocialPlatform, SocialSentiment],
        options_flow: Optional[FlowAnalysis]
    ) -> str:
        """Calculate overall sentiment momentum"""
        
        momentum_signals = []
        
        # News momentum
        if news_sentiment:
            if news_sentiment.sentiment_trend == "IMPROVING":
                momentum_signals.append(1)
            elif news_sentiment.sentiment_trend == "DETERIORATING":
                momentum_signals.append(-1)
            else:
                momentum_signals.append(0)
        
        # Social momentum
        for sentiment in social_sentiments.values():
            if sentiment.sentiment_momentum == "BUILDING":
                momentum_signals.append(1)
            elif sentiment.sentiment_momentum == "FADING":
                momentum_signals.append(-1)
            else:
                momentum_signals.append(0)
        
        # Options momentum (simplified - based on flow velocity)
        if options_flow:
            if options_flow.flow_velocity >= 10:  # High flow rate
                momentum_signals.append(1)
            elif options_flow.flow_velocity <= 2:  # Low flow rate
                momentum_signals.append(-1)
            else:
                momentum_signals.append(0)
        
        # Aggregate momentum
        if momentum_signals:
            avg_momentum = sum(momentum_signals) / len(momentum_signals)
            if avg_momentum >= 0.3:
                return "BUILDING"
            elif avg_momentum <= -0.3:
                return "FADING"
        
        return "STABLE"

    def _check_sentiment_divergence(self, news_score: float, social_score: float, options_score: float) -> bool:
        """Check for significant divergence between sentiment sources"""
        scores = [score for score in [news_score, social_score, options_score] if score != 0.0]
        
        if len(scores) <= 1:
            return False
        
        # Calculate standard deviation
        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        std_dev = variance ** 0.5
        
        # Significant divergence if standard deviation > 0.4
        return std_dev > 0.4

    def _determine_trading_implications(
        self,
        overall_sentiment: float,
        confidence: float,
        options_flow: Optional[FlowAnalysis],
        news_sentiment: Optional[InstrumentNewsSentiment]
    ) -> Tuple[str, str, str]:
        """Determine trading implications"""
        
        # Directional bias
        if overall_sentiment >= 0.2:
            bias = "BULLISH"
        elif overall_sentiment <= -0.2:
            bias = "BEARISH"
        else:
            bias = "NEUTRAL"
        
        # Conviction strength
        if confidence >= 0.7:
            conviction = "HIGH"
        elif confidence >= 0.4:
            conviction = "MEDIUM"
        else:
            conviction = "LOW"
        
        # Time horizon
        horizon = "MEDIUM"  # Default
        
        if options_flow:
            if options_flow.average_dte <= 7:
                horizon = "SHORT"  # Short-term options activity
            elif options_flow.average_dte >= 30:
                horizon = "LONG"   # Long-term options activity
        
        if news_sentiment:
            if news_sentiment.sentiment_trend in ["IMPROVING", "DETERIORATING"]:
                horizon = "SHORT"  # News-driven moves tend to be shorter term
        
        return bias, conviction, horizon

    def _create_neutral_sentiment(self, instrument: str, hours_back: int) -> MarketSentiment:
        """Create neutral sentiment when data is unavailable"""
        return MarketSentiment(
            instrument=instrument,
            timestamp=datetime.utcnow(),
            timeframe_minutes=hours_back * 60,
            overall_sentiment_score=0.0,
            confidence_level=0.0,
            sentiment_type=MarketSentimentType.NEUTRAL,
            news_sentiment=None,
            social_sentiments={},
            options_flow=None,
            news_weight=0.33,
            social_weight=0.33,
            options_weight=0.34,
            sentiment_drivers=["Dati sentiment non disponibili"],
            risk_factors=[],
            conviction_factors=[],
            sentiment_momentum="STABLE",
            sentiment_divergence=False,
            directional_bias="NEUTRAL",
            conviction_strength="LOW",
            time_horizon="MEDIUM",
            unusual_activity_detected=False,
            unusual_activities=[]
        )

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check cache validity"""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key]["timestamp"]
        return datetime.utcnow() - cached_time < self.cache_timeout

    async def cleanup(self):
        """Cleanup all resources"""
        await self.news_provider.cleanup()
        await self.social_analyzer.cleanup()
        await self.options_analyzer.cleanup()

    def format_sentiment_for_signal(self, sentiment: MarketSentiment) -> str:
        """Format sentiment analysis for integration in trading signals"""
        
        lines = []
        
        # Header
        lines.append(f"\n📈 ANALISI SENTIMENT ({sentiment.timeframe_minutes//60}h)")
        lines.append(f"• Sentiment Generale: {sentiment.sentiment_type.value}")
        lines.append(f"• Score Complessivo: {sentiment.overall_sentiment_score:.2f}/1.0")
        lines.append(f"• Livello Confidenza: {sentiment.confidence_level:.0%}")
        
        # Component breakdown
        if sentiment.news_sentiment:
            lines.append(f"\n📰 NEWS ({sentiment.news_weight:.0%} peso):")
            lines.append(f"• {sentiment.news_sentiment.articles_count} articoli, sentiment: {sentiment.news_sentiment.avg_sentiment_score:.2f}")
            lines.append(f"• Trend: {sentiment.news_sentiment.sentiment_trend}")
            if sentiment.news_sentiment.top_keywords:
                lines.append(f"• Keywords: {', '.join(sentiment.news_sentiment.top_keywords[:3])}")
        
        if sentiment.social_sentiments:
            lines.append(f"\n💬 SOCIAL MEDIA ({sentiment.social_weight:.0%} peso):")
            for platform, social in sentiment.social_sentiments.items():
                lines.append(f"• {platform.value}: {social.posts_count} posts, sentiment: {social.engagement_weighted_sentiment:.2f}")
        
        if sentiment.options_flow:
            lines.append(f"\n📊 FLUSSO OPZIONI ({sentiment.options_weight:.0%} peso):")
            lines.append(f"• Premium totale: ${sentiment.options_flow.total_premium_flow/1000:.0f}K")
            lines.append(f"• Bias istituzionale: {sentiment.options_flow.institutional_bias}")
            lines.append(f"• P/C Ratio: {sentiment.options_flow.put_call_ratio:.2f}")
        
        # Key insights
        if sentiment.sentiment_drivers:
            lines.append(f"\n🎯 FATTORI CHIAVE:")
            for driver in sentiment.sentiment_drivers[:3]:
                lines.append(f"• {driver}")
        
        # Trading implications
        lines.append(f"\n⚡ IMPLICAZIONI TRADING:")
        lines.append(f"• Bias Direzionale: {sentiment.directional_bias}")
        lines.append(f"• Forza Convinzione: {sentiment.conviction_strength}")
        lines.append(f"• Orizzonte Temporale: {sentiment.time_horizon}")
        
        if sentiment.sentiment_divergence:
            lines.append("• ⚠️ DIVERGENZA tra fonti sentiment rilevata")
        
        if sentiment.unusual_activity_detected:
            lines.append(f"• 🚨 {len(sentiment.unusual_activities)} attività inusuali rilevate")
        
        return "\n".join(lines)
