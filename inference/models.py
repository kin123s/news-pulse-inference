"""
Pydantic V2 Models with Custom Validators
엄격한 타입 안전성과 데이터 정규화 로직
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import (
    BaseModel, 
    Field, 
    field_validator, 
    model_validator,
    ConfigDict
)
import re


class SentimentType(str, Enum):
    """감성 타입"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    UNKNOWN = "unknown"


class NewsSource(BaseModel):
    """뉴스 출처"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=200)
    
    @field_validator('name')
    @classmethod
    def normalize_name(cls, v: str) -> str:
        """출처 이름 정규화"""
        # 특수문자 제거 및 공백 정리
        normalized = re.sub(r'[^\w\s-]', '', v)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized


class RawNewsArticle(BaseModel):
    """원본 뉴스 데이터 (Kafka에서 수신)"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True
    )
    
    id: str = Field(..., description="고유 식별자")
    source: NewsSource
    author: Optional[str] = Field(None, max_length=200)
    title: str = Field(..., min_length=10, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    content: Optional[str] = Field(None, max_length=10000)
    url: str = Field(..., pattern=r'^https?://.+')
    urlToImage: Optional[str] = Field(None, pattern=r'^https?://.+')
    publishedAt: str = Field(...)
    category: Optional[str] = Field(None, max_length=50)
    
    @field_validator('title', 'description', 'content')
    @classmethod
    def normalize_text(cls, v: Optional[str]) -> Optional[str]:
        """텍스트 정규화: 불필요한 공백 제거, HTML 태그 제거"""
        if not v:
            return v
        
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', v)
        # 연속된 공백을 하나로
        text = re.sub(r'\s+', ' ', text)
        # 특수 유니코드 문자 정리
        text = text.encode('utf-8', 'ignore').decode('utf-8')
        return text.strip()
    
    @field_validator('publishedAt')
    @classmethod
    def validate_datetime(cls, v: str) -> str:
        """날짜 형식 검증"""
        try:
            # ISO 8601 형식 검증
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid datetime format: {v}")
    
    @model_validator(mode='after')
    def validate_content_exists(self):
        """title 또는 content 중 하나는 반드시 존재해야 함"""
        if not self.title and not self.content:
            raise ValueError("Either title or content must be provided")
        return self


class AnalysisResult(BaseModel):
    """분석 결과"""
    model_config = ConfigDict(use_enum_values=True)
    
    sentiment: SentimentType = Field(default=SentimentType.UNKNOWN)
    sentiment_score: float = Field(default=0.0, ge=-1.0, le=1.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    keywords: List[str] = Field(default_factory=list, max_length=20)
    entities: List[Dict[str, Any]] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    model_version: str = Field(default="v1.0")
    inference_time_ms: float = Field(default=0.0, ge=0.0)
    
    @field_validator('keywords')
    @classmethod
    def normalize_keywords(cls, v: List[str]) -> List[str]:
        """키워드 정규화 및 중복 제거"""
        normalized = []
        seen = set()
        for keyword in v:
            # 소문자 변환 및 공백 제거
            kw = keyword.lower().strip()
            if kw and kw not in seen and len(kw) >= 3:
                normalized.append(kw)
                seen.add(kw)
        return normalized[:10]  # 최대 10개로 제한


class AnalyzedNewsArticle(BaseModel):
    """분석된 뉴스 (Redis 저장용)"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True
    )
    
    # 원본 데이터
    id: str
    source: NewsSource
    author: Optional[str] = None
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    url: str
    urlToImage: Optional[str] = None
    publishedAt: str
    category: Optional[str] = None
    
    # 분석 결과
    analysis: AnalysisResult
    
    # 메타데이터
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    pipeline_version: str = Field(default="v1.0")


class InferenceRequest(BaseModel):
    """추론 요청"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    text: str = Field(..., min_length=10, max_length=10000)
    model_name: Optional[str] = Field(default="default", max_length=50)
    options: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('text')
    @classmethod
    def normalize_text(cls, v: str) -> str:
        """텍스트 정규화"""
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', v)
        # 연속된 공백을 하나로
        text = re.sub(r'\s+', ' ', text)
        return text.strip()


class InferenceResponse(BaseModel):
    """추론 응답"""
    request_id: str
    result: AnalysisResult
    latency_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthCheck(BaseModel):
    """헬스체크 응답"""
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    kafka_connected: bool = False
    redis_connected: bool = False
    model_loaded: bool = False


class MetricsResponse(BaseModel):
    """메트릭 응답"""
    total_processed: int = 0
    success_rate: float = 0.0
    avg_latency_ms: float = 0.0
    active_connections: int = 0
    kafka_lag: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
