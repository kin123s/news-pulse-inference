"""
FastAPI Inference Server
실시간 뉴스 분석 추론 서버
- Prometheus 메트릭
- 헬스체크
- 동기/비동기 추론 API
"""
import asyncio
import time
import logging
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import (
    Counter, Histogram, Gauge, Summary,
    generate_latest, CONTENT_TYPE_LATEST
)

from .models import (
    RawNewsArticle,
    AnalyzedNewsArticle,
    InferenceRequest,
    InferenceResponse,
    HealthCheck,
    MetricsResponse
)
from .async_inference_engine import AsyncInferenceEngine

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus 메트릭 정의
inference_requests_total = Counter(
    'inference_requests_total',
    'Total number of inference requests',
    ['status']
)

inference_success_total = Counter(
    'inference_success_total',
    'Total number of successful inferences'
)

inference_failure_total = Counter(
    'inference_failure_total',
    'Total number of failed inferences',
    ['error_type']
)

inference_duration_seconds = Histogram(
    'inference_duration_seconds',
    'Inference processing time in seconds',
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

inference_batch_size = Histogram(
    'inference_batch_size',
    'Number of articles in batch inference',
    buckets=[1, 5, 10, 20, 50, 100]
)

active_inference_tasks = Gauge(
    'active_inference_tasks',
    'Number of currently running inference tasks'
)

kafka_consumer_lag = Gauge(
    'kafka_consumer_lag',
    'Kafka consumer lag'
)

model_load_status = Gauge(
    'model_load_status',
    'Model load status (1=loaded, 0=not loaded)'
)

inference_latency_summary = Summary(
    'inference_latency_ms',
    'Inference latency in milliseconds'
)

# 전역 변수
inference_engine: Optional[AsyncInferenceEngine] = None
total_processed = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 라이프사이클 관리"""
    global inference_engine
    
    # Startup
    logger.info("Starting FastAPI Inference Server...")
    
    # 추론 엔진 초기화
    inference_engine = AsyncInferenceEngine(
        openai_api_key=None,  # 환경변수에서 로드 가능
        max_concurrent_requests=20,
        timeout=30.0
    )
    
    model_load_status.set(1)
    logger.info("Inference engine initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Inference Server...")
    if inference_engine:
        await inference_engine.close()
    model_load_status.set(0)
    logger.info("Inference Server stopped")


# FastAPI 앱 생성
app = FastAPI(
    title="Real-time News Analysis Inference Server",
    description="고성능 비동기 스트림 처리 기반 뉴스 분석 엔진",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """루트 엔드포인트"""
    return {
        "service": "Real-time News Analysis Inference Server",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", response_model=HealthCheck, tags=["Health"])
async def health_check():
    """
    헬스체크 엔드포인트
    - 서비스 상태
    - 연결 상태
    - 모델 로드 상태
    """
    return HealthCheck(
        status="healthy",
        kafka_connected=True,  # 실제로는 Kafka 연결 체크
        redis_connected=True,  # 실제로는 Redis 연결 체크
        model_loaded=inference_engine is not None
    )


@app.get("/metrics", tags=["Metrics"])
async def metrics():
    """
    Prometheus 메트릭 엔드포인트
    /metrics 엔드포인트를 Prometheus가 스크랩
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/metrics/summary", response_model=MetricsResponse, tags=["Metrics"])
async def metrics_summary():
    """
    메트릭 요약 (JSON 형식)
    대시보드나 모니터링 도구에서 사용
    """
    global total_processed
    
    # 성공률 계산
    total_requests = inference_requests_total._value._value
    success_count = inference_success_total._value._value
    success_rate = (success_count / total_requests * 100) if total_requests > 0 else 0.0
    
    return MetricsResponse(
        total_processed=total_processed,
        success_rate=success_rate,
        avg_latency_ms=0.0,  # 실제 계산 필요
        active_connections=int(active_inference_tasks._value._value),
        kafka_lag=int(kafka_consumer_lag._value._value)
    )


@app.post(
    "/inference/single",
    response_model=AnalyzedNewsArticle,
    tags=["Inference"]
)
async def inference_single(article: RawNewsArticle):
    """
    단일 뉴스 분석
    
    - 하나의 뉴스를 받아 실시간 분석
    - 비동기 처리로 빠른 응답
    """
    if not inference_engine:
        raise HTTPException(status_code=503, detail="Inference engine not loaded")
    
    inference_requests_total.labels(status='single').inc()
    active_inference_tasks.inc()
    
    start_time = time.time()
    
    try:
        with inference_duration_seconds.time():
            analyzed = await inference_engine.analyze_single(
                article,
                use_external_api=False
            )
        
        inference_success_total.inc()
        
        elapsed_ms = (time.time() - start_time) * 1000
        inference_latency_summary.observe(elapsed_ms)
        
        global total_processed
        total_processed += 1
        
        logger.info(f"Single inference completed: {article.id} in {elapsed_ms:.2f}ms")
        
        return analyzed
    
    except Exception as e:
        inference_failure_total.labels(error_type=type(e).__name__).inc()
        logger.error(f"Inference failed for {article.id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        active_inference_tasks.dec()


@app.post(
    "/inference/batch",
    response_model=List[AnalyzedNewsArticle],
    tags=["Inference"]
)
async def inference_batch(articles: List[RawNewsArticle]):
    """
    배치 뉴스 분석
    
    - 여러 뉴스를 한 번에 받아 병렬 분석
    - asyncio.gather로 동시 처리
    - 최대 처리량 최적화
    """
    if not inference_engine:
        raise HTTPException(status_code=503, detail="Inference engine not loaded")
    
    if len(articles) == 0:
        raise HTTPException(status_code=400, detail="Empty article list")
    
    if len(articles) > 100:
        raise HTTPException(
            status_code=400, 
            detail="Batch size too large (max 100)"
        )
    
    inference_requests_total.labels(status='batch').inc()
    inference_batch_size.observe(len(articles))
    active_inference_tasks.inc()
    
    start_time = time.time()
    
    try:
        with inference_duration_seconds.time():
            analyzed_list = await inference_engine.analyze_batch(
                articles,
                use_external_api=False
            )
        
        inference_success_total.inc(len(analyzed_list))
        
        elapsed_ms = (time.time() - start_time) * 1000
        avg_latency = elapsed_ms / len(analyzed_list)
        
        global total_processed
        total_processed += len(analyzed_list)
        
        logger.info(
            f"Batch inference completed: {len(analyzed_list)}/{len(articles)} "
            f"articles in {elapsed_ms:.2f}ms (avg: {avg_latency:.2f}ms/article)"
        )
        
        return analyzed_list
    
    except Exception as e:
        inference_failure_total.labels(error_type=type(e).__name__).inc()
        logger.error(f"Batch inference failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        active_inference_tasks.dec()


@app.post("/inference/async", tags=["Inference"])
async def inference_async(
    articles: List[RawNewsArticle],
    background_tasks: BackgroundTasks
):
    """
    비동기 배치 분석
    
    - 요청을 받고 즉시 응답
    - 백그라운드에서 처리
    - 긴 배치 작업에 적합
    """
    if not inference_engine:
        raise HTTPException(status_code=503, detail="Inference engine not loaded")
    
    request_id = f"req_{int(time.time() * 1000)}"
    
    async def process_background():
        """백그라운드 처리"""
        try:
            await inference_engine.analyze_batch(articles, use_external_api=False)
            logger.info(f"Background task {request_id} completed")
        except Exception as e:
            logger.error(f"Background task {request_id} failed: {e}")
    
    background_tasks.add_task(process_background)
    
    return {
        "request_id": request_id,
        "status": "accepted",
        "article_count": len(articles),
        "message": "Processing in background"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )
