"""
Configuration for Inference Service
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class InferenceSettings(BaseSettings):
    """추론 서버 설정"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Server
    inference_host: str = "0.0.0.0"
    inference_port: int = 8000
    
    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_input_topic: str = "news_stream"
    kafka_output_topic: str = "analyzed_news"
    kafka_consumer_group: str = "inference_group"
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # AI APIs
    openai_api_key: Optional[str] = None
    huggingface_api_key: Optional[str] = None
    
    # Performance
    max_concurrent_requests: int = 20
    batch_size: int = 10
    batch_timeout: float = 2.0
    inference_timeout: float = 30.0
    
    # Monitoring
    enable_prometheus: bool = True
    prometheus_port: int = 8000
    
    # Model
    model_version: str = "v1.0"
    use_external_api: bool = False


def get_inference_settings() -> InferenceSettings:
    """설정 인스턴스 반환"""
    return InferenceSettings()
