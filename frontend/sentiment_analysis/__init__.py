"""
Sentiment Analysis Module v6.0
Real-time News, Social Media, and Options Flow Analysis
"""

__version__ = "6.0.0"
__author__ = "AI Trading System"

from .news_sentiment import NewsProvider, NewsSentimentAnalyzer
from .social_sentiment import SocialMediaAnalyzer, TwitterSentiment, RedditSentiment  
from .options_flow import OptionsFlowAnalyzer, FlowType, OptionsFlowData
from .sentiment_aggregator import SentimentAggregator, MarketSentiment

__all__ = [
    'NewsProvider',
    'NewsSentimentAnalyzer', 
    'SocialMediaAnalyzer',
    'TwitterSentiment',
    'RedditSentiment',
    'OptionsFlowAnalyzer',
    'FlowType',
    'OptionsFlowData',
    'SentimentAggregator',
    'MarketSentiment'
]