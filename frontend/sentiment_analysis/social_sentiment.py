"""
Social Media Sentiment Analysis
Integrazione con Twitter/X, Reddit, StockTwits per sentiment trading
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import logging
import json
import re
from collections import defaultdict

logger = logging.getLogger(__name__)

class SocialPlatform(Enum):
    TWITTER = "twitter"
    REDDIT = "reddit"  
    STOCKTWITS = "stocktwits"
    DISCORD = "discord"
    TELEGRAM = "telegram"

class PostType(Enum):
    TWEET = "tweet"
    REDDIT_POST = "reddit_post"
    REDDIT_COMMENT = "reddit_comment"
    STOCKTWITS_POST = "stocktwits_post"
    DISCORD_MESSAGE = "discord_message"

@dataclass
class SocialPost:
    """Singolo post social media"""
    id: str
    platform: SocialPlatform
    post_type: PostType
    content: str
    author: str
    author_followers: int
    author_verified: bool
    created_at: datetime
    engagement_score: float  # likes + retweets + comments weighted
    sentiment_score: float   # -1.0 to 1.0
    instruments_mentioned: List[str]
    hashtags: List[str]
    mentions: List[str]
    url: Optional[str] = None

@dataclass  
class SocialSentiment:
    """Sentiment aggregato per strumento da social media"""
    instrument: str
    platform: SocialPlatform
    timeframe_minutes: int
    posts_count: int
    total_engagement: int
    avg_sentiment_score: float
    engagement_weighted_sentiment: float
    bullish_posts: int
    bearish_posts: int
    neutral_posts: int
    top_hashtags: List[str]
    influencer_sentiment: float  # Sentiment from verified/high follower accounts
    viral_posts: List[SocialPost]  # High engagement posts
    sentiment_momentum: str  # "BUILDING", "FADING", "STABLE"

@dataclass
class TrendingTopic:
    """Topic trending sui social media"""
    keyword: str
    platform: SocialPlatform
    posts_count: int
    growth_rate: float  # % growth over last hour
    sentiment_score: float
    related_instruments: List[str]
    top_posts: List[SocialPost]

class TwitterSentiment:
    """Twitter/X sentiment analysis (simulato - richiede API keys)"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Trading-related hashtags e keywords
        self.trading_hashtags = {
            "SPX500_USD": ["$SPY", "$SPX", "#SP500", "#stocks", "#trading"],
            "NAS100_USD": ["$QQQ", "$NASDAQ", "#NASDAQ", "#tech", "#stocks"],
            "US30_USD": ["$DIA", "$DOW", "#DowJones", "#stocks"],
            "EUR_USD": ["$EURUSD", "#EURUSD", "#forex", "#euro", "#dollar"],
            "GBP_USD": ["$GBPUSD", "#GBPUSD", "#forex", "#pound", "#cable"],
            "XAU_USD": ["$GOLD", "#gold", "#XAU", "#preciousmetals"],
            "XAG_USD": ["$SILVER", "#silver", "#XAG", "#preciousmetals"]
        }
        
        # Influential traders/accounts to monitor (example handles)
        self.influential_accounts = [
            "zerohedge", "unusual_whales", "spotgamma", "optionshawk",
            "investingcom", "marketwatch", "bloomberg", "cnbc"
        ]

    async def get_session(self) -> aiohttp.ClientSession:
        """Get aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

    async def fetch_twitter_sentiment(self, instrument: str, hours_back: int = 6) -> List[SocialPost]:
        """Fetch Twitter posts for instrument (simulato)"""
        posts = []
        
        try:
            # Simulate Twitter API calls (in production would use actual Twitter API v2)
            hashtags = self.trading_hashtags.get(instrument, [f"${instrument}"])
            
            for hashtag in hashtags[:3]:  # Top 3 hashtags
                # Generate simulated tweets
                for i in range(np.random.randint(5, 15)):
                    post = self._generate_simulated_tweet(instrument, hashtag)
                    posts.append(post)
                    
        except Exception as e:
            logger.error(f"Error fetching Twitter sentiment: {e}")
        
        return posts

    def _generate_simulated_tweet(self, instrument: str, hashtag: str) -> SocialPost:
        """Generate realistic simulated tweet"""
        
        # Sample tweet contents (realistic trading tweets)
        tweet_templates = [
            f"{hashtag} looking bullish on the daily chart. Breaking resistance! 📈 #trading",
            f"Bearish divergence on {hashtag}. Time to be cautious 📉 #analysis", 
            f"{hashtag} consolidating at key level. Waiting for breakout direction 🤔",
            f"Just entered long {hashtag}. Risk management is key! 💪 #daytrading",
            f"Market makers playing games with {hashtag} again 🎭 #manipulation",
            f"Strong volume on {hashtag} today. Something's brewing... 👀",
            f"{hashtag} hitting major resistance. Could bounce or break through 🤷‍♂️"
        ]
        
        content = np.random.choice(tweet_templates)
        
        # Random engagement metrics
        engagement = np.random.exponential(100)  # Exponential distribution for realistic engagement
        
        return SocialPost(
            id=f"tweet_{np.random.randint(100000, 999999)}",
            platform=SocialPlatform.TWITTER,
            post_type=PostType.TWEET,
            content=content,
            author=f"trader_{np.random.randint(1000, 9999)}",
            author_followers=np.random.randint(100, 50000),
            author_verified=np.random.random() < 0.1,  # 10% chance verified
            created_at=datetime.utcnow() - timedelta(minutes=np.random.randint(1, 360)),
            engagement_score=engagement,
            sentiment_score=self._calculate_post_sentiment(content),
            instruments_mentioned=[instrument],
            hashtags=[hashtag, "#trading"],
            mentions=[],
            url=f"https://x.com/tweet/{np.random.randint(100000, 999999)}"
        )

    def _calculate_post_sentiment(self, content: str) -> float:
        """Calculate sentiment from post content"""
        content_lower = content.lower()
        
        bullish_words = ["bullish", "moon", "pump", "long", "buy", "breakout", "surge", "rally", "📈", "🚀", "💪"]
        bearish_words = ["bearish", "dump", "short", "sell", "crash", "drop", "breakdown", "fall", "📉", "💩", "⬇️"]
        
        bullish_count = sum(1 for word in bullish_words if word in content_lower)
        bearish_count = sum(1 for word in bearish_words if word in content_lower)
        
        # Normalize sentiment
        total_sentiment_words = bullish_count + bearish_count
        if total_sentiment_words == 0:
            return np.random.uniform(-0.2, 0.2)  # Slight random for neutral posts
        
        return (bullish_count - bearish_count) / total_sentiment_words

class RedditSentiment:
    """Reddit sentiment analysis"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Relevant subreddits for trading sentiment
        self.trading_subreddits = [
            "wallstreetbets", "investing", "stocks", "SecurityAnalysis", 
            "ValueInvesting", "options", "forex", "daytrading", "pennystocks"
        ]
        
        # Keywords for different instruments
        self.reddit_keywords = {
            "SPX500_USD": ["spy", "spx", "s&p500", "market", "stocks"],
            "NAS100_USD": ["qqq", "nasdaq", "tech", "apple", "microsoft"],
            "XAU_USD": ["gold", "gld", "mining", "inflation", "precious"],
            "EUR_USD": ["euro", "eurusd", "forex", "ecb", "fed"]
        }

    async def fetch_reddit_sentiment(self, instrument: str, hours_back: int = 12) -> List[SocialPost]:
        """Fetch Reddit posts and comments"""
        posts = []
        
        try:
            # Simulate Reddit API calls (would use PRAW in production)
            keywords = self.reddit_keywords.get(instrument, [instrument.lower()])
            
            for subreddit in self.trading_subreddits[:3]:  # Top 3 subreddits
                for keyword in keywords[:2]:  # Top 2 keywords
                    # Generate simulated Reddit posts
                    post = self._generate_simulated_reddit_post(instrument, subreddit, keyword)
                    posts.append(post)
                    
                    # Add some comments
                    for _ in range(np.random.randint(0, 3)):
                        comment = self._generate_simulated_reddit_comment(instrument, subreddit)
                        posts.append(comment)
                        
        except Exception as e:
            logger.error(f"Error fetching Reddit sentiment: {e}")
        
        return posts

    def _generate_simulated_reddit_post(self, instrument: str, subreddit: str, keyword: str) -> SocialPost:
        """Generate simulated Reddit post"""
        
        post_templates = [
            f"DD: Why {keyword.upper()} is heading to the moon 🚀",
            f"Technical Analysis: {keyword.upper()} - Bullish or Bearish?",
            f"YOLO: Just went all in on {keyword.upper()}. Am I retarded?",
            f"Discussion: What are your thoughts on {keyword.upper()} current levels?",
            f"News: Major catalyst coming for {keyword.upper()} this week",
            f"Loss/Gain: My {keyword.upper()} position update - down 50% but holding 💎🙌"
        ]
        
        title = np.random.choice(post_templates)
        
        return SocialPost(
            id=f"reddit_{subreddit}_{np.random.randint(100000, 999999)}",
            platform=SocialPlatform.REDDIT,
            post_type=PostType.REDDIT_POST,
            content=title,
            author=f"u/trader_{np.random.randint(100, 9999)}",
            author_followers=0,  # Reddit doesn't have followers
            author_verified=False,
            created_at=datetime.utcnow() - timedelta(hours=np.random.randint(1, 12)),
            engagement_score=np.random.randint(10, 1000),  # Upvotes
            sentiment_score=self._calculate_reddit_sentiment(title),
            instruments_mentioned=[instrument],
            hashtags=[],
            mentions=[],
            url=f"https://reddit.com/r/{subreddit}/comments/{np.random.randint(100000, 999999)}"
        )

    def _generate_simulated_reddit_comment(self, instrument: str, subreddit: str) -> SocialPost:
        """Generate simulated Reddit comment"""
        
        comment_templates = [
            "This is the way! 💎🙌",
            "Positions or ban",
            "To the moon! 🚀🚀🚀",
            "Buy the dip, retard",
            "This aged well... NOT",
            "Technical analysis is astrology for men",
            "HODL gang where you at?",
            "Sir, this is a casino"
        ]
        
        content = np.random.choice(comment_templates)
        
        return SocialPost(
            id=f"comment_{subreddit}_{np.random.randint(100000, 999999)}",
            platform=SocialPlatform.REDDIT,
            post_type=PostType.REDDIT_COMMENT,
            content=content,
            author=f"u/ape_{np.random.randint(100, 9999)}",
            author_followers=0,
            author_verified=False,
            created_at=datetime.utcnow() - timedelta(hours=np.random.randint(1, 8)),
            engagement_score=np.random.randint(1, 100),
            sentiment_score=self._calculate_reddit_sentiment(content),
            instruments_mentioned=[instrument],
            hashtags=[],
            mentions=[],
            url=f"https://reddit.com/r/{subreddit}/comments/{np.random.randint(100000, 999999)}"
        )

    def _calculate_reddit_sentiment(self, content: str) -> float:
        """Calculate Reddit-specific sentiment"""
        content_lower = content.lower()
        
        # Reddit-specific bullish terms
        bullish = ["moon", "rocket", "diamond", "hands", "hodl", "buy", "dip", "yolo", "calls", "🚀", "💎", "🙌"]
        bearish = ["crash", "puts", "short", "sell", "dump", "bear", "gay", "rekt", "loss", "bag", "holding"]
        
        bullish_count = sum(1 for word in bullish if word in content_lower)
        bearish_count = sum(1 for word in bearish if word in content_lower)
        
        if bullish_count == 0 and bearish_count == 0:
            return 0.0
        
        return (bullish_count - bearish_count) / (bullish_count + bearish_count)


class SocialMediaAnalyzer:
    """Main analyzer aggregating social media sentiment"""
    
    def __init__(self):
        self.twitter = TwitterSentiment()
        self.reddit = RedditSentiment() 
        self.cache = {}
        self.cache_timeout = timedelta(minutes=15)  # Shorter cache for social media

    async def get_aggregated_sentiment(self, instrument: str, hours_back: int = 6) -> Dict[SocialPlatform, SocialSentiment]:
        """Get aggregated sentiment from all platforms"""
        
        # Check cache
        cache_key = f"{instrument}_{hours_back}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]["data"]
        
        sentiments = {}
        
        # Fetch from all platforms in parallel
        tasks = [
            self._analyze_platform_sentiment(SocialPlatform.TWITTER, instrument, hours_back),
            self._analyze_platform_sentiment(SocialPlatform.REDDIT, instrument, hours_back)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, SocialSentiment):
                platform = [SocialPlatform.TWITTER, SocialPlatform.REDDIT][i]
                sentiments[platform] = result
            elif isinstance(result, Exception):
                logger.error(f"Social sentiment error: {result}")
        
        # Cache results
        self.cache[cache_key] = {
            "data": sentiments,
            "timestamp": datetime.utcnow()
        }
        
        return sentiments

    async def _analyze_platform_sentiment(self, platform: SocialPlatform, instrument: str, hours_back: int) -> SocialSentiment:
        """Analyze sentiment for specific platform"""
        
        if platform == SocialPlatform.TWITTER:
            posts = await self.twitter.fetch_twitter_sentiment(instrument, hours_back)
        elif platform == SocialPlatform.REDDIT:
            posts = await self.reddit.fetch_reddit_sentiment(instrument, hours_back)
        else:
            posts = []
        
        if not posts:
            return SocialSentiment(
                instrument=instrument,
                platform=platform,
                timeframe_minutes=hours_back * 60,
                posts_count=0,
                total_engagement=0,
                avg_sentiment_score=0.0,
                engagement_weighted_sentiment=0.0,
                bullish_posts=0,
                bearish_posts=0,
                neutral_posts=0,
                top_hashtags=[],
                influencer_sentiment=0.0,
                viral_posts=[],
                sentiment_momentum="STABLE"
            )
        
        # Calculate aggregated metrics
        total_engagement = sum(post.engagement_score for post in posts)
        avg_sentiment = sum(post.sentiment_score for post in posts) / len(posts)
        
        # Engagement-weighted sentiment
        if total_engagement > 0:
            engagement_weighted = sum(post.sentiment_score * post.engagement_score for post in posts) / total_engagement
        else:
            engagement_weighted = avg_sentiment
        
        # Count sentiment distribution
        bullish = sum(1 for post in posts if post.sentiment_score > 0.1)
        bearish = sum(1 for post in posts if post.sentiment_score < -0.1)
        neutral = len(posts) - bullish - bearish
        
        # Top hashtags
        all_hashtags = []
        for post in posts:
            all_hashtags.extend(post.hashtags)
        
        hashtag_counts = defaultdict(int)
        for tag in all_hashtags:
            hashtag_counts[tag] += 1
        
        top_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_hashtags = [tag[0] for tag in top_hashtags]
        
        # Influencer sentiment (verified accounts or high followers)
        influencer_posts = [p for p in posts if p.author_verified or p.author_followers > 10000]
        influencer_sentiment = 0.0
        if influencer_posts:
            influencer_sentiment = sum(p.sentiment_score for p in influencer_posts) / len(influencer_posts)
        
        # Viral posts (top engagement)
        viral_posts = sorted(posts, key=lambda x: x.engagement_score, reverse=True)[:3]
        
        # Sentiment momentum (simple calculation)
        momentum = "STABLE"
        if len(posts) >= 4:
            recent_posts = posts[:len(posts)//2]
            older_posts = posts[len(posts)//2:]
            
            recent_sentiment = sum(p.sentiment_score for p in recent_posts) / len(recent_posts)
            older_sentiment = sum(p.sentiment_score for p in older_posts) / len(older_posts)
            
            if recent_sentiment > older_sentiment + 0.1:
                momentum = "BUILDING"
            elif recent_sentiment < older_sentiment - 0.1:
                momentum = "FADING"
        
        return SocialSentiment(
            instrument=instrument,
            platform=platform,
            timeframe_minutes=hours_back * 60,
            posts_count=len(posts),
            total_engagement=int(total_engagement),
            avg_sentiment_score=avg_sentiment,
            engagement_weighted_sentiment=engagement_weighted,
            bullish_posts=bullish,
            bearish_posts=bearish,
            neutral_posts=neutral,
            top_hashtags=top_hashtags,
            influencer_sentiment=influencer_sentiment,
            viral_posts=viral_posts,
            sentiment_momentum=momentum
        )

    def get_trending_topics(self) -> List[TrendingTopic]:
        """Get trending topics across platforms (simplified)"""
        # Simulate trending topics
        trending = [
            TrendingTopic(
                keyword="$SPY",
                platform=SocialPlatform.TWITTER,
                posts_count=1250,
                growth_rate=23.5,
                sentiment_score=0.3,
                related_instruments=["SPX500_USD"],
                top_posts=[]
            ),
            TrendingTopic(
                keyword="Gold",
                platform=SocialPlatform.REDDIT,
                posts_count=420,
                growth_rate=15.2,
                sentiment_score=0.6,
                related_instruments=["XAU_USD"],
                top_posts=[]
            )
        ]
        
        return trending

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache is valid"""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key]["timestamp"]
        return datetime.utcnow() - cached_time < self.cache_timeout

    async def cleanup(self):
        """Cleanup resources"""
        if self.twitter.session:
            await self.twitter.session.close()
        if self.reddit.session:
            await self.reddit.session.close()