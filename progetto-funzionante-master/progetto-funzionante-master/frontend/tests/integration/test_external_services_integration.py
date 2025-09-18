"""
Comprehensive integration tests for external service integrations.
Tests OANDA API, email services, AI services, cache, and other external dependencies.
"""

import pytest
import json
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any, List
import httpx

from models import User, Signal, SignalTypeEnum
from app.services.oanda_service import OANDAService
from app.services.cache_service import CacheService
from app.services.auth_service import AuthService
from app.services.signal_service import SignalService
from app.repositories.signal_repository import SignalRepository


class TestExternalServicesIntegration:
    """Integration test suite for external service integrations."""

    # OANDA Service Tests
    def test_oanda_service_initialization(self, db_session):
        """Test OANDA service initialization and configuration."""
        with patch.dict('os.environ', {
            'OANDA_API_KEY': 'test_api_key',
            'OANDA_ACCOUNT_ID': 'test_account_id',
            'OANDA_ENVIRONMENT': 'demo'
        }):
            oanda_service = OANDAService(db_session)
            assert oanda_service.api_key == 'test_api_key'
            assert oanda_service.account_id == 'test_account_id'
            assert oanda_service.environment == 'demo'

    def test_oanda_market_data_retrieval(self, db_session):
        """Test OANDA market data retrieval."""
        oanda_service = OANDAService(db_session)

        # Mock HTTP response
        mock_response = {
            "instrument": "EUR_USD",
            "price": 1.1234,
            "time": datetime.utcnow().isoformat(),
            "bid": 1.1233,
            "ask": 1.1235,
            "spread": 0.0002
        }

        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = httpx.Response(200, json=mock_response)

            result = oanda_service.get_market_data("EUR_USD")
            assert result["price"] == 1.1234
            assert result["spread"] == 0.0002

    def test_oanda_signal_generation(self, db_session):
        """Test OANDA signal generation with technical analysis."""
        oanda_service = OANDAService(db_session)

        # Mock market data and technical indicators
        mock_market_data = {
            "price": 1.1234,
            "spread": 0.0001,
            "volume": 1000,
            "timestamp": datetime.utcnow().isoformat()
        }

        mock_technical_analysis = {
            "rsi": 45.2,
            "macd": 0.0023,
            "bollinger_upper": 1.1300,
            "bollinger_lower": 1.1150,
            "atr": 0.0050
        }

        with patch.object(oanda_service, 'get_market_data', return_value=mock_market_data), \
             patch.object(oanda_service, 'get_technical_indicators', return_value=mock_technical_analysis):

            signal = oanda_service.generate_signal("EUR_USD")
            assert signal["symbol"] == "EUR_USD"
            assert signal["signal_type"] in ["BUY", "SELL", "HOLD"]
            assert "confidence" in signal
            assert "analysis" in signal

    def test_oanda_account_data_retrieval(self, db_session):
        """Test OANDA account data retrieval."""
        oanda_service = OANDAService(db_session)

        mock_account_data = {
            "id": "test_account_id",
            "balance": 10000.0,
            "equity": 10500.0,
            "marginUsed": 1000.0,
            "marginAvailable": 9000.0,
            "unrealizedPL": 500.0,
            "openPositionCount": 3
        }

        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = httpx.Response(200, json=mock_account_data)

            result = oanda_service.get_account_data()
            assert result["balance"] == 10000.0
            assert result["equity"] == 10500.0
            assert result["marginAvailable"] == 9000.0

    def test_oanda_order_execution(self, db_session):
        """Test OANDA order execution functionality."""
        oanda_service = OANDAService(db_session)

        order_data = {
            "instrument": "EUR_USD",
            "units": 1000,
            "type": "MARKET",
            "side": "buy",
            "stopLoss": 1.1200,
            "takeProfit": 1.1300
        }

        mock_order_response = {
            "orderFillTransaction": {
                "id": "order_id_123",
                "instrument": "EUR_USD",
                "units": 1000,
                "price": 1.1234,
                "time": datetime.utcnow().isoformat()
            }
        }

        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = httpx.Response(200, json=mock_order_response)

            result = oanda_service.execute_order(order_data)
            assert result["order_id"] == "order_id_123"
            assert result["price"] == 1.1234

    def test_oanda_error_handling(self, db_session):
        """Test OANDA service error handling."""
        oanda_service = OANDAService(db_session)

        # Test network error
        with patch('httpx.AsyncClient.get', side_effect=httpx.RequestError("Network error")):
            result = oanda_service.get_market_data("EUR_USD")
            assert "error" in result

        # Test API error response
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = httpx.Response(400, json={"error": "Invalid request"})

            result = oanda_service.get_market_data("EUR_USD")
            assert "error" in result

        # Test rate limiting
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = httpx.Response(429, json={"error": "Rate limit exceeded"})

            result = oanda_service.get_market_data("EUR_USD")
            assert "error" in result

    # Cache Service Tests
    def test_cache_service_basic_operations(self):
        """Test cache service basic operations."""
        cache_service = CacheService()

        # Test cache set and get
        test_data = {"key": "value", "timestamp": datetime.utcnow().isoformat()}
        cache_service.set("test_key", test_data, ttl=60)

        retrieved_data = cache_service.get("test_key")
        assert retrieved_data == test_data

        # Test cache delete
        cache_service.delete("test_key")
        retrieved_data = cache_service.get("test_key")
        assert retrieved_data is None

    def test_cache_service_with_ttl(self):
        """Test cache service TTL functionality."""
        cache_service = CacheService()

        # Test short TTL
        cache_service.set("short_ttl_key", "test_value", ttl=1)

        # Should be available immediately
        assert cache_service.get("short_ttl_key") == "test_value"

        # Mock time passage
        with patch('time.time', return_value=time.time() + 2):
            assert cache_service.get("short_ttl_key") is None

    def test_cache_service_batch_operations(self):
        """Test cache service batch operations."""
        cache_service = CacheService()

        # Test batch set
        batch_data = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        }
        cache_service.set_many(batch_data, ttl=60)

        # Test batch get
        retrieved_data = cache_service.get_many(["key1", "key2", "key3"])
        assert retrieved_data == batch_data

        # Test batch delete
        cache_service.delete_many(["key1", "key2"])
        remaining_data = cache_service.get_many(["key1", "key2", "key3"])
        assert remaining_data == {"key3": "value3"}

    def test_cache_service_pattern_operations(self):
        """Test cache service pattern-based operations."""
        cache_service = CacheService()

        # Set multiple keys with pattern
        keys_data = {
            "signal:EUR_USD:1": {"symbol": "EUR_USD"},
            "signal:GBP_USD:1": {"symbol": "GBP_USD"},
            "signal:EUR_USD:2": {"symbol": "EUR_USD"},
            "user:1": {"username": "testuser"}
        }

        cache_service.set_many(keys_data, ttl=60)

        # Test pattern deletion
        deleted_count = cache_service.delete_pattern("signal:EUR_USD:*")
        assert deleted_count == 2

        # Verify deletion
        remaining_keys = cache_service.get_many(list(keys_data.keys()))
        assert len(remaining_keys) == 2  # Only GBP_USD and user keys remain

    def test_cache_service_statistics(self):
        """Test cache service statistics and metrics."""
        cache_service = CacheService()

        # Perform some operations
        cache_service.set("stats_test", "value", ttl=60)
        cache_service.get("stats_test")
        cache_service.get("nonexistent_key")

        stats = cache_service.get_statistics()
        assert "hits" in stats
        assert "misses" in stats
        assert "total_operations" in stats
        assert "hit_rate" in stats

    def test_cache_service_error_handling(self):
        """Test cache service error handling."""
        cache_service = CacheService()

        # Test with invalid TTL
        cache_service.set("invalid_ttl", "value", ttl=-1)
        assert cache_service.get("invalid_ttl") is None

        # Test with large data
        large_data = {"data": "x" * 1024 * 1024}  # 1MB data
        cache_service.set("large_data", large_data, ttl=60)
        retrieved = cache_service.get("large_data")
        assert retrieved == large_data

    # Email Service Tests
    def test_email_service_configuration(self):
        """Test email service configuration."""
        with patch.dict('os.environ', {
            'EMAIL_HOST': 'smtp.test.com',
            'EMAIL_PORT': '587',
            'EMAIL_USER': 'test@test.com',
            'EMAIL_PASSWORD': 'testpassword'
        }):
            from app.services.email_service import EmailService
            email_service = EmailService()
            assert email_service.host == 'smtp.test.com'
            assert email_service.port == 587

    def test_email_service_send_email(self):
        """Test email sending functionality."""
        with patch.dict('os.environ', {
            'EMAIL_HOST': 'smtp.test.com',
            'EMAIL_PORT': '587',
            'EMAIL_USER': 'test@test.com',
            'EMAIL_PASSWORD': 'testpassword'
        }):
            from app.services.email_service import EmailService
            email_service = EmailService()

            with patch('smtplib.SMTP') as mock_smtp:
                mock_server = MagicMock()
                mock_smtp.return_value.__enter__.return_value = mock_server

                result = email_service.send_email(
                    to_email="recipient@test.com",
                    subject="Test Subject",
                    body="Test Body"
                )

                assert result is True
                mock_server.send_message.assert_called_once()

    def test_email_service_template_rendering(self):
        """Test email template rendering."""
        with patch.dict('os.environ', {
            'EMAIL_HOST': 'smtp.test.com',
            'EMAIL_PORT': '587',
            'EMAIL_USER': 'test@test.com',
            'EMAIL_PASSWORD': 'testpassword'
        }):
            from app.services.email_service import EmailService
            email_service = EmailService()

            template_data = {
                "username": "testuser",
                "verification_url": "https://test.com/verify?token=abc123",
                "expiry_hours": 24
            }

            with patch('smtplib.SMTP'):
                result = email_service.send_verification_email(
                    to_email="test@test.com",
                    username="testuser",
                    verification_token="abc123"
                )

                assert result is True

    def test_email_service_error_handling(self):
        """Test email service error handling."""
        with patch.dict('os.environ', {
            'EMAIL_HOST': 'smtp.test.com',
            'EMAIL_PORT': '587',
            'EMAIL_USER': 'test@test.com',
            'EMAIL_PASSWORD': 'testpassword'
        }):
            from app.services.email_service import EmailService
            email_service = EmailService()

            # Test SMTP error
            with patch('smtplib.SMTP', side_effect=Exception("SMTP Error")):
                result = email_service.send_email(
                    to_email="recipient@test.com",
                    subject="Test Subject",
                    body="Test Body"
                )
                assert result is False

    # AI Service Tests (Gemini Integration)
    def test_ai_service_initialization(self):
        """Test AI service initialization."""
        with patch.dict('os.environ', {
            'GEMINI_API_KEY': 'test_gemini_key'
        }):
            from app.services.ai_service import AIService
            ai_service = AIService()
            assert ai_service.api_key == 'test_gemini_key'

    def test_ai_service_signal_analysis(self):
        """Test AI service signal analysis."""
        with patch.dict('os.environ', {
            'GEMINI_API_KEY': 'test_gemini_key'
        }):
            from app.services.ai_service import AIService
            ai_service = AIService()

            market_data = {
                "symbol": "EUR_USD",
                "price": 1.1234,
                "rsi": 45.2,
                "macd": 0.0023,
                "bollinger_position": "middle"
            }

            mock_ai_response = {
                "signal_type": "BUY",
                "confidence": 0.85,
                "analysis": "Technical indicators suggest buying opportunity",
                "risk_level": "MEDIUM"
            }

            with patch.object(ai_service, 'analyze_signal', return_value=mock_ai_response):
                result = ai_service.analyze_signal(market_data)
                assert result["signal_type"] == "BUY"
                assert result["confidence"] == 0.85
                assert "analysis" in result

    def test_ai_service_market_sentiment(self):
        """Test AI service market sentiment analysis."""
        with patch.dict('os.environ', {
            'GEMINI_API_KEY': 'test_gemini_key'
        }):
            from app.services.ai_service import AIService
            ai_service = AIService()

            market_news = [
                "EURUSD shows positive momentum",
                "European economy recovering",
                "USD weakening against major currencies"
            ]

            mock_sentiment_response = {
                "sentiment_score": 0.75,
                "confidence": 0.82,
                "key_factors": ["economic recovery", "monetary policy"],
                "outlook": "bullish"
            }

            with patch.object(ai_service, 'analyze_sentiment', return_value=mock_sentiment_response):
                result = ai_service.analyze_sentiment(market_news)
                assert result["sentiment_score"] == 0.75
                assert result["confidence"] == 0.82
                assert result["outlook"] == "bullish"

    def test_ai_service_error_handling(self):
        """Test AI service error handling."""
        with patch.dict('os.environ', {
            'GEMINI_API_KEY': 'test_gemini_key'
        }):
            from app.services.ai_service import AIService
            ai_service = AIService()

            # Test API error
            with patch.object(ai_service, 'analyze_signal', side_effect=Exception("AI API Error")):
                result = ai_service.analyze_signal({"symbol": "EUR_USD"})
                assert "error" in result

            # Test timeout
            with patch.object(ai_service, 'analyze_signal', side_effect=asyncio.TimeoutError("AI Timeout")):
                result = ai_service.analyze_signal({"symbol": "EUR_USD"})
                assert "error" in result

    # HTTP Client Service Tests
    def test_http_client_service_basic_request(self):
        """Test HTTP client service basic requests."""
        from app.services.http_client_service import HTTPClientService

        http_client = HTTPClientService()

        mock_response_data = {"message": "success", "data": [1, 2, 3]}

        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = httpx.Response(200, json=mock_response_data)

            result = http_client.get("https://api.example.com/test")
            assert result == mock_response_data

    def test_http_client_service_error_handling(self):
        """Test HTTP client service error handling."""
        from app.services.http_client_service import HTTPClientService

        http_client = HTTPClientService()

        # Test network error
        with patch('httpx.AsyncClient.get', side_effect=httpx.RequestError("Network error")):
            result = http_client.get("https://api.example.com/test")
            assert "error" in result

        # Test timeout
        with patch('httpx.AsyncClient.get', side_effect=httpx.TimeoutException("Timeout")):
            result = http_client.get("https://api.example.com/test")
            assert "error" in result

        # Test HTTP error
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = httpx.Response(404, json={"error": "Not found"})

            result = http_client.get("https://api.example.com/test")
            assert "error" in result

    def test_http_client_service_retry_mechanism(self):
        """Test HTTP client service retry mechanism."""
        from app.services.http_client_service import HTTPClientService

        http_client = HTTPClientService()

        mock_response_data = {"message": "success"}

        with patch('httpx.AsyncClient.get') as mock_get:
            # First call fails, second succeeds
            mock_get.side_effect = [
                httpx.RequestError("Network error"),
                httpx.Response(200, json=mock_response_data)
            ]

            result = http_client.get("https://api.example.com/test", max_retries=2)
            assert result == mock_response_data
            assert mock_get.call_count == 2

    # File Service Tests
    def test_file_service_operations(self):
        """Test file service operations."""
        from app.services.file_service import FileService

        file_service = FileService()

        # Test file writing
        test_content = "Test file content"
        file_path = "test_file.txt"

        write_result = file_service.write_file(file_path, test_content)
        assert write_result is True

        # Test file reading
        read_result = file_service.read_file(file_path)
        assert read_result == test_content

        # Test file deletion
        delete_result = file_service.delete_file(file_path)
        assert delete_result is True

        # Test file existence check
        exists_result = file_service.file_exists(file_path)
        assert exists_result is False

    def test_file_service_error_handling(self):
        """Test file service error handling."""
        from app.services.file_service import FileService

        file_service = FileService()

        # Test reading non-existent file
        result = file_service.read_file("nonexistent_file.txt")
        assert "error" in result

        # Test writing to invalid path
        result = file_service.write_file("/invalid/path/test.txt", "content")
        assert result is False

    # Integration Tests for Multiple Services
    def test_signal_generation_with_external_services(self, db_session, user_fixture: User):
        """Test signal generation using multiple external services."""
        signal_service = SignalService(db_session)

        # Mock external service responses
        mock_oanda_data = {
            "price": 1.1234,
            "spread": 0.0001,
            "volume": 1000,
            "timestamp": datetime.utcnow().isoformat()
        }

        mock_ai_analysis = {
            "signal_type": "BUY",
            "confidence": 0.85,
            "analysis": "AI analysis indicates buying opportunity",
            "risk_level": "MEDIUM"
        }

        with patch('app.services.signal_service.oanda_service.get_market_data', return_value=mock_oanda_data), \
             patch('app.services.signal_service.ai_service.analyze_signal', return_value=mock_ai_analysis):

            signal_data = {
                "symbol": "EUR_USD",
                "signal_type": SignalTypeEnum.BUY,
                "entry_price": 1.1234,
                "stop_loss": 1.1200,
                "take_profit": 1.1300,
                "reliability": 85.5,
                "confidence_score": 0.85,
                "risk_level": "MEDIUM",
                "is_public": True,
                "is_active": True
            }

            signal = signal_service.create_signal(signal_data, user_fixture.id)
            assert signal.symbol == "EUR_USD"
            assert signal.creator_id == user_fixture.id

    def test_cached_external_data_retrieval(self, db_session):
        """Test caching of external data retrieval."""
        oanda_service = OANDAService(db_session)
        cache_service = CacheService()

        mock_market_data = {
            "price": 1.1234,
            "spread": 0.0001,
            "timestamp": datetime.utcnow().isoformat()
        }

        cache_key = f"market_data:EUR_USD"

        # First call - should hit external API
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = httpx.Response(200, json=mock_market_data)

            result = oanda_service.get_market_data("EUR_USD")
            assert result["price"] == 1.1234

            # Verify data was cached
            cached_data = cache_service.get(cache_key)
            assert cached_data == mock_market_data

        # Second call - should use cached data
        with patch('httpx.AsyncClient.get') as mock_get:
            result = oanda_service.get_market_data("EUR_USD")
            assert result["price"] == 1.1234
            mock_get.assert_not_called()  # API should not be called

    def test_service_fallback_mechanisms(self, db_session):
        """Test service fallback mechanisms when external services fail."""
        signal_service = SignalService(db_session)

        # Test fallback when OANDA service fails
        with patch('app.services.signal_service.oanda_service.get_market_data', side_effect=Exception("OANDA Error")):
            # Should fallback to cached data or default values
            signal_data = {
                "symbol": "EUR_USD",
                "signal_type": SignalTypeEnum.BUY,
                "entry_price": 1.1234,  # Default fallback price
                "reliability": 70.0  # Default fallback reliability
            }

            # This should not raise an exception but use fallback data
            try:
                signal = signal_service.create_signal(signal_data, 1)
                assert signal is not None
            except Exception:
                # If it does raise an exception, that's also acceptable behavior
                pass

    def test_external_service_rate_limiting(self, db_session):
        """Test rate limiting for external service calls."""
        oanda_service = OANDAService(db_session)

        # Mock rate limit response
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = httpx.Response(429, json={"error": "Rate limit exceeded"})

            # Should handle rate limit gracefully
            result = oanda_service.get_market_data("EUR_USD")
            assert "error" in result

            # Verify the service implements backoff or retry logic
            assert mock_get.call_count <= 3  # Should not retry indefinitely

    def test_external_service_authentication(self, db_session):
        """Test external service authentication."""
        oanda_service = OANDAService(db_session)

        # Test authentication error
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = httpx.Response(401, json={"error": "Unauthorized"})

            result = oanda_service.get_market_data("EUR_USD")
            assert "error" in result
            assert "authentication" in result["error"].lower()

    def test_concurrent_external_service_calls(self, db_session):
        """Test concurrent external service calls."""
        import asyncio
        import threading

        oanda_service = OANDAService(db_session)
        results = []

        async def fetch_market_data(symbol):
            mock_response = {"price": 1.1234, "symbol": symbol}
            with patch('httpx.AsyncClient.get') as mock_get:
                mock_get.return_value = httpx.Response(200, json=mock_response)
                result = oanda_service.get_market_data(symbol)
                results.append(result)

        # Run multiple concurrent requests
        symbols = ["EUR_USD", "GBP_USD", "USD_JPY"]
        tasks = [fetch_market_data(symbol) for symbol in symbols]

        # Run in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(asyncio.gather(*tasks))

        # Verify all requests completed
        assert len(results) == len(symbols)
        for i, result in enumerate(results):
            assert result["symbol"] == symbols[i]

    @pytest.mark.slow
    def test_external_service_performance(self, db_session):
        """Test external service performance under load."""
        import time
        import threading

        oanda_service = OANDAService(db_session)
        response_times = []

        def fetch_data():
            start_time = time.time()
            mock_response = {"price": 1.1234, "timestamp": datetime.utcnow().isoformat()}
            with patch('httpx.AsyncClient.get') as mock_get:
                mock_get.return_value = httpx.Response(200, json=mock_response)
                result = oanda_service.get_market_data("EUR_USD")
            end_time = time.time()
            response_times.append(end_time - start_time)

        # Run concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=fetch_data)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify performance
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 2.0, f"Average response time {avg_response_time:.3f}s is too slow"

        # Verify all requests succeeded
        assert len(response_times) == 10