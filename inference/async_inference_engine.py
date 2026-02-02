"""
고성능 비동기 추론 엔진
asyncio.gather를 활용한 I/O 바운드 병목 최소화
"""
import asyncio
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .models import (
    RawNewsArticle, 
    AnalyzedNewsArticle, 
    AnalysisResult,
    SentimentType
)

logger = logging.getLogger(__name__)


class AsyncInferenceEngine:
    """
    비동기 추론 엔진
    - asyncio.gather로 다중 API 호출 병렬 처리
    - Retry 로직으로 안정성 확보
    - Rate limiting으로 API 제한 준수
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        hf_api_key: Optional[str] = None,
        max_concurrent_requests: int = 10,
        timeout: float = 30.0
    ):
        self.openai_api_key = openai_api_key
        self.hf_api_key = hf_api_key
        self.max_concurrent_requests = max_concurrent_requests
        self.timeout = timeout
        
        # Rate limiting semaphore
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        
        # HTTP 클라이언트 (connection pooling)
        self.http_client = httpx.AsyncClient(
            timeout=timeout,
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100
            )
        )
        
        logger.info(
            f"AsyncInferenceEngine initialized: "
            f"max_concurrent={max_concurrent_requests}, timeout={timeout}s"
        )
    
    async def analyze_batch(
        self, 
        articles: List[RawNewsArticle],
        use_external_api: bool = False
    ) -> List[AnalyzedNewsArticle]:
        """
        뉴스 배치를 병렬로 분석
        
        Args:
            articles: 원본 뉴스 리스트
            use_external_api: 외부 API 사용 여부
        
        Returns:
            분석된 뉴스 리스트
        """
        start_time = time.time()
        
        # asyncio.gather로 모든 분석 작업을 병렬 실행
        tasks = [
            self.analyze_single(article, use_external_api) 
            for article in articles
        ]
        
        # return_exceptions=True로 일부 실패해도 계속 진행
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 성공한 결과만 필터링
        analyzed_articles = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"Failed to analyze article {articles[i].id}: {result}"
                )
            else:
                analyzed_articles.append(result)
        
        elapsed_time = (time.time() - start_time) * 1000
        success_rate = len(analyzed_articles) / len(articles) * 100
        
        logger.info(
            f"Batch analysis completed: {len(analyzed_articles)}/{len(articles)} "
            f"successful ({success_rate:.1f}%), {elapsed_time:.2f}ms"
        )
        
        return analyzed_articles
    
    async def analyze_single(
        self, 
        article: RawNewsArticle,
        use_external_api: bool = False
    ) -> AnalyzedNewsArticle:
        """
        단일 뉴스 분석 (병렬 처리 가능)
        
        Args:
            article: 원본 뉴스
            use_external_api: 외부 API 사용 여부
        
        Returns:
            분석된 뉴스
        """
        start_time = time.time()
        
        # Semaphore로 동시 실행 제한
        async with self.semaphore:
            try:
                # 여러 분석 작업을 병렬로 실행
                if use_external_api and self.openai_api_key:
                    # 외부 API 사용 (OpenAI, HuggingFace 등)
                    sentiment_task = self._analyze_sentiment_external(article)
                    keywords_task = self._extract_keywords_external(article)
                    entities_task = self._extract_entities_external(article)
                    
                    # 병렬 실행
                    sentiment_result, keywords, entities = await asyncio.gather(
                        sentiment_task,
                        keywords_task,
                        entities_task,
                        return_exceptions=True
                    )
                    
                    # 예외 처리
                    if isinstance(sentiment_result, Exception):
                        logger.warning(f"Sentiment analysis failed: {sentiment_result}")
                        sentiment_result = self._analyze_sentiment_local(article)
                    
                    if isinstance(keywords, Exception):
                        logger.warning(f"Keyword extraction failed: {keywords}")
                        keywords = self._extract_keywords_local(article)
                    
                    if isinstance(entities, Exception):
                        logger.warning(f"Entity extraction failed: {entities}")
                        entities = []
                
                else:
                    # 로컬 분석 (빠르고 안정적)
                    sentiment_result = self._analyze_sentiment_local(article)
                    keywords = self._extract_keywords_local(article)
                    entities = []
                
                # 중요도 점수 계산
                importance_score = self._calculate_importance(
                    article, 
                    sentiment_result
                )
                
                # 분석 결과 생성
                inference_time_ms = (time.time() - start_time) * 1000
                
                analysis = AnalysisResult(
                    sentiment=sentiment_result['sentiment'],
                    sentiment_score=sentiment_result['score'],
                    confidence=sentiment_result.get('confidence', 0.8),
                    keywords=keywords,
                    entities=entities,
                    importance_score=importance_score,
                    analyzed_at=datetime.utcnow(),
                    model_version="v1.0-async",
                    inference_time_ms=inference_time_ms
                )
                
                # 분석된 뉴스 생성
                analyzed_article = AnalyzedNewsArticle(
                    id=article.id,
                    source=article.source,
                    author=article.author,
                    title=article.title,
                    description=article.description,
                    content=article.content,
                    url=article.url,
                    urlToImage=article.urlToImage,
                    publishedAt=article.publishedAt,
                    category=article.category,
                    analysis=analysis
                )
                
                logger.debug(
                    f"Article {article.id} analyzed: "
                    f"sentiment={analysis.sentiment}, "
                    f"time={inference_time_ms:.2f}ms"
                )
                
                return analyzed_article
                
            except Exception as e:
                logger.error(f"Error analyzing article {article.id}: {e}")
                raise
    
    def _analyze_sentiment_local(self, article: RawNewsArticle) -> Dict[str, Any]:
        """로컬 감성 분석 (빠른 휴리스틱 기반)"""
        text = f"{article.title} {article.description or ''} {article.content or ''}"
        text = text.lower()
        
        # 감성 키워드
        positive_words = {
            'good', 'great', 'excellent', 'amazing', 'positive', 'success',
            'win', 'growth', 'improve', 'innovative', 'breakthrough', 'gain',
            'rise', 'surge', 'boom', 'profit', 'achieve'
        }
        
        negative_words = {
            'bad', 'worst', 'terrible', 'negative', 'fail', 'loss', 'decline',
            'crisis', 'crash', 'collapse', 'drop', 'concern', 'risk', 'threat',
            'fall', 'plunge', 'damage', 'harm', 'danger'
        }
        
        words = set(text.split())
        pos_count = len(words & positive_words)
        neg_count = len(words & negative_words)
        
        if pos_count > neg_count:
            sentiment = SentimentType.POSITIVE
            score = min((pos_count - neg_count) / 10, 1.0)
        elif neg_count > pos_count:
            sentiment = SentimentType.NEGATIVE
            score = max((pos_count - neg_count) / 10, -1.0)
        else:
            sentiment = SentimentType.NEUTRAL
            score = 0.0
        
        return {
            'sentiment': sentiment,
            'score': score,
            'confidence': 0.7
        }
    
    def _extract_keywords_local(self, article: RawNewsArticle) -> List[str]:
        """로컬 키워드 추출"""
        import re
        from collections import Counter
        
        text = f"{article.title} {article.description or ''}"
        
        # 불용어
        stop_words = {
            'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but',
            'in', 'with', 'to', 'for', 'of', 'as', 'by', 'that', 'this', 'it',
            'from', 'be', 'are', 'was', 'were', 'been', 'have', 'has', 'had'
        }
        
        # 단어 추출 (4글자 이상)
        words = re.findall(r'\b\w{4,}\b', text.lower())
        filtered = [w for w in words if w not in stop_words]
        
        # 빈도 계산
        counter = Counter(filtered)
        keywords = [word for word, _ in counter.most_common(10)]
        
        return keywords
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _analyze_sentiment_external(
        self, 
        article: RawNewsArticle
    ) -> Dict[str, Any]:
        """외부 API를 사용한 감성 분석 (OpenAI 등)"""
        if not self.openai_api_key:
            return self._analyze_sentiment_local(article)
        
        # OpenAI API 호출 예시 (실제 구현은 프로젝트에 맞게 조정)
        text = f"{article.title}. {article.description or ''}"
        
        # 실제로는 OpenAI API를 호출
        # 여기서는 데모를 위해 로컬 분석 결과 반환
        await asyncio.sleep(0.1)  # API 호출 시뮬레이션
        return self._analyze_sentiment_local(article)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _extract_keywords_external(
        self, 
        article: RawNewsArticle
    ) -> List[str]:
        """외부 API를 사용한 키워드 추출"""
        await asyncio.sleep(0.1)  # API 호출 시뮬레이션
        return self._extract_keywords_local(article)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _extract_entities_external(
        self, 
        article: RawNewsArticle
    ) -> List[Dict[str, Any]]:
        """외부 API를 사용한 개체명 인식"""
        await asyncio.sleep(0.1)  # API 호출 시뮬레이션
        return []
    
    def _calculate_importance(
        self, 
        article: RawNewsArticle,
        sentiment_result: Dict[str, Any]
    ) -> float:
        """뉴스 중요도 점수 계산"""
        score = 0.5
        
        # 감성 강도에 따른 점수
        score += abs(sentiment_result['score']) * 0.2
        
        # 제목 길이
        if len(article.title) > 50:
            score += 0.1
        
        # 설명 존재 여부
        if article.description:
            score += 0.1
        
        # 이미지 존재 여부
        if article.urlToImage:
            score += 0.1
        
        return min(score, 1.0)
    
    async def close(self):
        """리소스 정리"""
        await self.http_client.aclose()
        logger.info("AsyncInferenceEngine closed")
