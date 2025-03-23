import pytest
from unittest.mock import MagicMock, patch
from app.cache import get_cached_url, cache_url, delete_cached_url
import redis

@pytest.fixture
def mock_redis():
    with patch("app.cache.redis_client") as mock:
        mock.get.return_value = None
        mock.setex.return_value = True
        mock.delete.return_value = 1
        yield mock

def test_cache_hit(mock_redis):
    mock_redis.get.return_value = b"http://cached.com"
    result = get_cached_url("test")
    assert result == "http://cached.com"
    mock_redis.get.assert_called_with("url:test")

def test_cache_miss(mock_redis):
    result = get_cached_url("missing")
    assert result is None
    mock_redis.get.assert_called_with("url:missing")

def test_cache_url(mock_redis):
    cache_url("test", "http://example.com", 60)
    mock_redis.setex.assert_called_with("url:test", 60, "http://example.com")

def test_cache_delete(mock_redis):
    delete_cached_url("test")
    mock_redis.delete.assert_called_with("url:test")

def test_cache_connection_error(mock_redis):
    mock_redis.get.side_effect = redis.ConnectionError("Connection error")
    result = get_cached_url("test")
    assert result is None
    mock_redis.get.assert_called_with("url:test")

def test_cache_expiration(mock_redis):
    cache_url("expiring", "http://expire.com", ttl=1)
    mock_redis.setex.assert_called_with("url:expiring", 1, "http://expire.com")

def test_cache_connection_failure_on_set(mock_redis):
    mock_redis.setex.side_effect = redis.ConnectionError("Connection failed")
    cache_url("test", "http://example.com", 60)
    mock_redis.setex.assert_called_with("url:test", 60, "http://example.com")

def test_cache_delete_failure(mock_redis):
    mock_redis.delete.side_effect = redis.ConnectionError("Delete failed")
    delete_cached_url("test")
    mock_redis.delete.assert_called_with("url:test")


