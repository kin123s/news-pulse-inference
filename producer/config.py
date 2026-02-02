"""
Configuration module for the news analysis system
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Kafka Settings
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "news_stream"
    
    # Redis Settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # News API Settings
    news_api_key: str = ""
    news_api_url: str = "https://newsapi.org/v2/top-headlines"
    
    # Service Ports
    producer_port: int = 8001
    consumer_port: int = 8002
    
    # WebSocket Settings
    ws_connections_max: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings():
    return Settings()
