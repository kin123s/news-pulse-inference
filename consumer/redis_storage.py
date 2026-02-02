"""
Redis storage service for analyzed news
"""
import json
import logging
from typing import Dict, Any, List, Optional
import redis

logger = logging.getLogger(__name__)


class RedisStorage:
    def __init__(self, host: str, port: int, db: int):
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True
        )
        logger.info(f"Redis client initialized: {host}:{port}/{db}")
    
    def store_analysis(self, news_id: str, analysis_data: Dict[str, Any]) -> bool:
        """Store analyzed news in Redis"""
        try:
            key = f"news:analysis:{news_id}"
            value = json.dumps(analysis_data)
            
            # Store with expiration (7 days)
            self.client.setex(key, 604800, value)
            
            # Add to sorted set by importance score
            importance = analysis_data.get('analysis', {}).get('importance_score', 0)
            self.client.zadd('news:by_importance', {news_id: importance})
            
            # Add to recent news list
            self.client.lpush('news:recent', news_id)
            self.client.ltrim('news:recent', 0, 99)  # Keep last 100
            
            logger.info(f"Stored analysis for news: {news_id}")
            return True
            
        except redis.RedisError as e:
            logger.error(f"Redis error storing analysis: {e}")
            return False
    
    def get_analysis(self, news_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve analyzed news from Redis"""
        try:
            key = f"news:analysis:{news_id}"
            value = self.client.get(key)
            
            if value:
                return json.loads(value)
            return None
            
        except redis.RedisError as e:
            logger.error(f"Redis error retrieving analysis: {e}")
            return None
    
    def get_recent_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent analyzed news"""
        try:
            news_ids = self.client.lrange('news:recent', 0, limit - 1)
            results = []
            
            for news_id in news_ids:
                analysis = self.get_analysis(news_id)
                if analysis:
                    results.append(analysis)
            
            return results
            
        except redis.RedisError as e:
            logger.error(f"Redis error getting recent news: {e}")
            return []
    
    def get_top_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top news by importance score"""
        try:
            # Get top scored news IDs
            news_ids = self.client.zrevrange('news:by_importance', 0, limit - 1)
            results = []
            
            for news_id in news_ids:
                analysis = self.get_analysis(news_id)
                if analysis:
                    results.append(analysis)
            
            return results
            
        except redis.RedisError as e:
            logger.error(f"Redis error getting top news: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about stored news"""
        try:
            return {
                "total_analyzed": self.client.zcard('news:by_importance'),
                "recent_count": self.client.llen('news:recent')
            }
        except redis.RedisError as e:
            logger.error(f"Redis error getting stats: {e}")
            return {}
    
    def close(self):
        """Close Redis connection"""
        self.client.close()
        logger.info("Redis connection closed")
