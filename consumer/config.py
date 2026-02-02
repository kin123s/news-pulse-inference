"""
Configuration module for the consumer service
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Kafka Settings
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "news_stream"
    kafka_group_id: str = "news_consumer_group"
    
    # Redis Settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Service Port
    consumer_port: int = 8002
    
    # WebSocket Settings
    ws_connections_max: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings():
    return Settings()
