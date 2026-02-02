"""
News API client for fetching news articles
"""
import httpx
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class NewsAPIClient:
    def __init__(self, api_key: str, api_url: str):
        self.api_key = api_key
        self.api_url = api_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def fetch_news(self, country: str = "us", category: str = "technology") -> List[Dict[str, Any]]:
        """
        Fetch news from external API
        
        Args:
            country: Country code (e.g., 'us', 'kr')
            category: News category (e.g., 'technology', 'business')
        
        Returns:
            List of news articles
        """
        try:
            params = {
                "apiKey": self.api_key,
                "country": country,
                "category": category,
                "pageSize": 20
            }
            
            response = await self.client.get(self.api_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get("articles", [])
            
            # Transform to our format
            transformed_articles = []
            for idx, article in enumerate(articles):
                transformed_articles.append({
                    "id": f"{article.get('publishedAt', '')}_{idx}",
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "content": article.get("content", ""),
                    "url": article.get("url", ""),
                    "source": article.get("source", {}).get("name", ""),
                    "publishedAt": article.get("publishedAt", ""),
                    "author": article.get("author", "")
                })
            
            logger.info(f"Fetched {len(transformed_articles)} articles")
            return transformed_articles
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching news: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            return []
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
