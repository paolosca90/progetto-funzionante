"""
Real-time News Sentiment Analysis
Integrazione con fonti news finanziarie per sentiment in tempo reale
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import json
import re

logger = logging.getLogger(__name__)

class SentimentPolarity(Enum):
    VERY_BEARISH = -2
    BEARISH = -1
    NEUTRAL = 0
    BULLISH = 1
    VERY_BULLISH = 2

class NewsSource(Enum):
    REUTERS = "reuters"
    BLOOMBERG = "bloomberg"
    CNBC = "cnbc"
    MARKETWATCH = "marketwatch"
    YAHOO_FINANCE = "yahoo"
    FINVIZ = "finviz"
    FT = "ft"

@dataclass
class NewsArticle:
    """Singolo articolo di news"""
    title: str
    content: str
    source: NewsSource
    published_at: datetime
    url: str
    instruments_mentioned: List[str]
    sentiment_score: float  # -1.0 to 1.0
    sentiment_polarity: SentimentPolarity
    relevance_score: float  # 0.0 to 1.0
    keywords: List[str]

@dataclass
class InstrumentNewsSentiment:
    """Sentiment aggregato per strumento"""
    instrument: str
    timeframe_minutes: int
    articles_count: int
    avg_sentiment_score: float
    sentiment_polarity: SentimentPolarity
    relevance_weighted_sentiment: float
    bullish_articles: int
    bearish_articles: int
    neutral_articles: int
    top_keywords: List[str]
    latest_articles: List[NewsArticle]
    sentiment_trend: str  # "IMPROVING", "DETERIORATING", "STABLE"

class NewsProvider:
    """Fornisce feed di news finanziarie da multiple fonti"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Keywords per rilevamento strumenti finanziari
        self.instrument_keywords = {
            # Forex
            "EUR_USD": ["euro", "dollar", "eurusd", "eur/usd", "eur-usd", "ecb", "fed"],
            "GBP_USD": ["pound", "sterling", "cable", "gbpusd", "gbp/usd", "boe"],
            "USD_JPY": ["yen", "usdjpy", "usd/jpy", "boj", "japan"],
            "AUD_USD": ["aussie", "audusd", "aud/usd", "rba", "australia"],
            
            # Indices  
            "SPX500_USD": ["s&p 500", "spx", "spy", "s&p500", "us stocks", "wall street"],
            "NAS100_USD": ["nasdaq", "qqq", "tech stocks", "technology", "apple", "microsoft"],
            "US30_USD": ["dow jones", "djia", "dow", "industrial"],
            "DE30_EUR": ["dax", "germany", "deutsche", "european stocks"],
            
            # Metals
            "XAU_USD": ["gold", "xauusd", "xau/usd", "precious metals", "gold price"],
            "XAG_USD": ["silver", "xagusd", "xag/usd", "precious metals"]
        }
        
        # Sentiment keywords
        self.bullish_keywords = [
            "rally", "surge", "soar", "bullish", "optimistic", "positive", "gains", 
            "upside", "breakthrough", "strong", "robust", "growth", "recovery",
            "buying", "demand", "support", "momentum", "breakout"
        ]
        
        self.bearish_keywords = [
            "crash", "plunge", "dive", "bearish", "pessimistic", "negative", "losses",
            "downside", "weakness", "decline", "recession", "fears", "concerns",
            "selling", "dump", "resistance", "breakdown", "correction"
        ]

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

    async def fetch_yahoo_finance_news(self, instruments: List[str]) -> List[NewsArticle]:
        """Fetch news da Yahoo Finance (free API)"""
        articles = []
        
        try:
            session = await self.get_session()
            
            for instrument in instruments:
                # Convert OANDA symbols to Yahoo symbols
                yahoo_symbol = self._convert_to_yahoo_symbol(instrument)
                if not yahoo_symbol:
                    continue
                    
                url = f"https://query1.finance.yahoo.com/v1/finance/search"
                params = {
                    "q": yahoo_symbol,
                    "quotes_count": 5,
                    "news_count": 10
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if "news" in data:
                            for news_item in data["news"][:5]:  # Top 5 news
                                article = self._parse_yahoo_news(news_item, instrument)
                                if article:
                                    articles.append(article)
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)
                
        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance news: {e}")
        
        return articles

    async def fetch_finviz_sentiment(self, instruments: List[str]) -> List[NewsArticle]:
        """Fetch sentiment da Finviz (web scraping simulato)"""
        articles = []
        
        try:
            # Simulate finviz data (in production would scrape actual site)
            for instrument in instruments:
                # Generate simulated news sentiment
                article = NewsArticle(
                    title=f"Market Analysis: {instrument} Shows Mixed Signals",
                    content=f"Technical analysis of {instrument} reveals conflicting indicators...",
                    source=NewsSource.FINVIZ,
                    published_at=datetime.utcnow() - timedelta(minutes=np.random.randint(5, 120)),
                    url=f"https://finviz.com/quote.ashx?t={instrument}",
                    instruments_mentioned=[instrument],
                    sentiment_score=np.random.uniform(-0.8, 0.8),
                    sentiment_polarity=self._score_to_polarity(np.random.uniform(-0.8, 0.8)),
                    relevance_score=np.random.uniform(0.6, 1.0),
                    keywords=["technical", "analysis", "signals"]
                )
                articles.append(article)
                
        except Exception as e:
            logger.error(f"Error fetching Finviz sentiment: {e}")
        
        return articles

    async def get_latest_news(self, instruments: List[str], hours_back: int = 6) -> List[NewsArticle]:
        """Get latest news per gli strumenti specificati"""
        all_articles = []
        
        # Fetch da multiple sources in parallel
        tasks = [
            self.fetch_yahoo_finance_news(instruments),
            self.fetch_finviz_sentiment(instruments)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"News fetch error: {result}")
        
        # Filter by timeframe
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        recent_articles = [a for a in all_articles if a.published_at > cutoff_time]
        
        # Sort by relevance and recency
        recent_articles.sort(key=lambda x: (x.relevance_score, x.published_at), reverse=True)
        
        return recent_articles

    def _convert_to_yahoo_symbol(self, oanda_symbol: str) -> Optional[str]:
        """Convert OANDA symbol to Yahoo Finance symbol"""
        conversions = {
            "SPX500_USD": "^GSPC",
            "NAS100_USD": "^IXIC", 
            "US30_USD": "^DJI",
            "XAU_USD": "GC=F",
            "XAG_USD": "SI=F",
            "EUR_USD": "EURUSD=X",
            "GBP_USD": "GBPUSD=X",
            "USD_JPY": "JPY=X"
        }
        return conversions.get(oanda_symbol)

    def _parse_yahoo_news(self, news_item: dict, instrument: str) -> Optional[NewsArticle]:
        """Parse Yahoo Finance news item"""
        try:
            title = news_item.get("title", "")
            content = news_item.get("summary", "")
            
            # Calculate sentiment
            sentiment_score = self._calculate_text_sentiment(f"{title} {content}")
            
            return NewsArticle(
                title=title,
                content=content,
                source=NewsSource.YAHOO_FINANCE,
                published_at=datetime.fromtimestamp(news_item.get("providerPublishTime", 0)),
                url=news_item.get("link", ""),
                instruments_mentioned=[instrument],
                sentiment_score=sentiment_score,
                sentiment_polarity=self._score_to_polarity(sentiment_score),
                relevance_score=self._calculate_relevance(title, content, instrument),
                keywords=self._extract_keywords(f"{title} {content}")
            )
            
        except Exception as e:
            logger.error(f"Error parsing Yahoo news: {e}")
            return None

    def _calculate_text_sentiment(self, text: str) -> float:
        """Simple sentiment calculation basato su keywords"""
        text_lower = text.lower()
        
        bullish_count = sum(1 for word in self.bullish_keywords if word in text_lower)
        bearish_count = sum(1 for word in self.bearish_keywords if word in text_lower)
        
        total_words = len(text.split())
        if total_words == 0:
            return 0.0
        
        # Normalize to -1.0 to 1.0 range
        sentiment = (bullish_count - bearish_count) / max(total_words * 0.1, 1)
        return max(-1.0, min(1.0, sentiment))

    def _score_to_polarity(self, score: float) -> SentimentPolarity:
        """Convert numeric score to sentiment polarity"""
        if score >= 0.6:
            return SentimentPolarity.VERY_BULLISH
        elif score >= 0.2:
            return SentimentPolarity.BULLISH
        elif score <= -0.6:
            return SentimentPolarity.VERY_BEARISH
        elif score <= -0.2:
            return SentimentPolarity.BEARISH
        else:
            return SentimentPolarity.NEUTRAL

    def _calculate_relevance(self, title: str, content: str, instrument: str) -> float:
        """Calculate relevance of news to instrument"""
        text = f"{title} {content}".lower()
        keywords = self.instrument_keywords.get(instrument, [])
        
        if not keywords:
            return 0.5  # Default relevance
        
        matches = sum(1 for keyword in keywords if keyword.lower() in text)
        return min(1.0, matches / len(keywords) * 2)  # Max 1.0

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        
        # Filter common words
        stop_words = {"that", "this", "with", "from", "they", "been", "have", "were", "said"}
        keywords = [w for w in words if w not in stop_words]
        
        # Return top 10 most relevant
        return list(set(keywords))[:10]

    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()


class NewsSentimentAnalyzer:
    """Analizza il sentiment delle news per strumenti finanziari"""
    
    def __init__(self, news_provider: NewsProvider):
        self.news_provider = news_provider
        self.cache = {}
        self.cache_timeout = timedelta(minutes=30)

    async def get_instrument_sentiment(self, instrument: str, timeframe_minutes: int = 360) -> InstrumentNewsSentiment:
        """Get sentiment aggregato per strumento"""
        
        # Check cache
        cache_key = f"{instrument}_{timeframe_minutes}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]["data"]
        
        # Fetch fresh news
        articles = await self.news_provider.get_latest_news([instrument], hours_back=timeframe_minutes//60)
        
        # Filter articles relevant to this instrument
        relevant_articles = [
            a for a in articles 
            if instrument in a.instruments_mentioned and a.relevance_score > 0.3
        ]
        
        if not relevant_articles:
            # Return neutral sentiment if no relevant articles
            sentiment = InstrumentNewsSentiment(
                instrument=instrument,
                timeframe_minutes=timeframe_minutes,
                articles_count=0,
                avg_sentiment_score=0.0,
                sentiment_polarity=SentimentPolarity.NEUTRAL,
                relevance_weighted_sentiment=0.0,
                bullish_articles=0,
                bearish_articles=0,
                neutral_articles=0,
                top_keywords=[],
                latest_articles=[],
                sentiment_trend="STABLE"
            )
        else:
            sentiment = self._calculate_aggregated_sentiment(relevant_articles, instrument, timeframe_minutes)
        
        # Cache result
        self.cache[cache_key] = {
            "data": sentiment,
            "timestamp": datetime.utcnow()
        }
        
        return sentiment

    def _calculate_aggregated_sentiment(self, articles: List[NewsArticle], instrument: str, timeframe_minutes: int) -> InstrumentNewsSentiment:
        """Calculate aggregated sentiment da multiple articles"""
        
        # Basic counts
        bullish = sum(1 for a in articles if a.sentiment_polarity.value > 0)
        bearish = sum(1 for a in articles if a.sentiment_polarity.value < 0)
        neutral = len(articles) - bullish - bearish
        
        # Weighted sentiment (by relevance)
        if articles:
            avg_sentiment = sum(a.sentiment_score for a in articles) / len(articles)
            relevance_weighted = sum(a.sentiment_score * a.relevance_score for a in articles) / sum(a.relevance_score for a in articles)
        else:
            avg_sentiment = 0.0
            relevance_weighted = 0.0
        
        # Aggregate keywords
        all_keywords = []
        for article in articles:
            all_keywords.extend(article.keywords)
        
        # Count keyword frequency
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        # Top keywords
        top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_keywords = [k[0] for k in top_keywords]
        
        # Sentiment trend (simplified)
        trend = "STABLE"
        if len(articles) >= 3:
            recent_sentiment = sum(a.sentiment_score for a in articles[:len(articles)//2]) / (len(articles)//2)
            older_sentiment = sum(a.sentiment_score for a in articles[len(articles)//2:]) / (len(articles) - len(articles)//2)
            
            if recent_sentiment > older_sentiment + 0.1:
                trend = "IMPROVING"
            elif recent_sentiment < older_sentiment - 0.1:
                trend = "DETERIORATING"
        
        return InstrumentNewsSentiment(
            instrument=instrument,
            timeframe_minutes=timeframe_minutes,
            articles_count=len(articles),
            avg_sentiment_score=avg_sentiment,
            sentiment_polarity=self.news_provider._score_to_polarity(avg_sentiment),
            relevance_weighted_sentiment=relevance_weighted,
            bullish_articles=bullish,
            bearish_articles=bearish,
            neutral_articles=neutral,
            top_keywords=top_keywords,
            latest_articles=articles[:5],  # Top 5 most recent
            sentiment_trend=trend
        )

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key]["timestamp"]
        return datetime.utcnow() - cached_time < self.cache_timeout
