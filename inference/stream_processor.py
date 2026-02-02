"""
Faust-Streaming 기반 스트림 프로세서
Kafka 스트림 처리를 위한 고성능 비동기 워커
"""
import faust
import asyncio
import logging
from typing import Optional
from datetime import datetime

from .models import RawNewsArticle, AnalyzedNewsArticle
from .async_inference_engine import AsyncInferenceEngine

logger = logging.getLogger(__name__)


class NewsStreamProcessor:
    """
    Faust 기반 뉴스 스트림 프로세서
    - Kafka에서 뉴스를 실시간으로 소비
    - 비동기 추론 엔진으로 분석
    - 결과를 다시 Kafka로 전송
    """
    
    def __init__(
        self,
        app_name: str = "news-stream-processor",
        broker: str = "kafka://localhost:9092",
        input_topic: str = "news_stream",
        output_topic: str = "analyzed_news",
        store_uri: str = "rocksdb://",
        openai_api_key: Optional[str] = None,
        max_concurrent: int = 10
    ):
        # Faust 앱 생성
        self.app = faust.App(
            app_name,
            broker=broker,
            store=store_uri,
            # 성능 최적화 설정
            stream_buffer_maxsize=1024,
            stream_wait_empty=False,
            producer_max_request_size=10485760,  # 10MB
            web_enabled=True,
            web_port=6066,
        )
        
        # 토픽 정의
        self.input_topic = self.app.topic(
            input_topic,
            value_type=bytes,  # JSON으로 직렬화된 바이트
        )
        
        self.output_topic = self.app.topic(
            output_topic,
            value_type=bytes,
        )
        
        # 추론 엔진
        self.inference_engine = AsyncInferenceEngine(
            openai_api_key=openai_api_key,
            max_concurrent_requests=max_concurrent
        )
        
        # 메트릭
        self.processed_count = 0
        self.error_count = 0
        
        # Agent 등록
        self._register_agents()
        
        logger.info(
            f"NewsStreamProcessor initialized: "
            f"broker={broker}, input={input_topic}, output={output_topic}"
        )
    
    def _register_agents(self):
        """Faust Agent 등록"""
        
        @self.app.agent(self.input_topic)
        async def process_news_stream(stream):
            """
            메인 스트림 프로세싱 Agent
            - Kafka에서 뉴스를 소비
            - 배치 처리로 성능 최적화
            - 분석 결과를 output topic으로 전송
            """
            batch = []
            batch_size = 10
            batch_timeout = 2.0  # 2초
            last_flush = asyncio.get_event_loop().time()
            
            async for raw_data in stream:
                try:
                    # JSON 파싱
                    import json
                    news_dict = json.loads(raw_data)
                    
                    # Pydantic 모델로 변환 (validation)
                    article = RawNewsArticle(**news_dict)
                    batch.append(article)
                    
                    current_time = asyncio.get_event_loop().time()
                    
                    # 배치가 가득 찼거나 타임아웃이면 처리
                    if (
                        len(batch) >= batch_size or 
                        (current_time - last_flush) >= batch_timeout
                    ):
                        # 배치 분석
                        analyzed = await self.inference_engine.analyze_batch(
                            batch,
                            use_external_api=False
                        )
                        
                        # 결과 전송
                        for analyzed_article in analyzed:
                            await self._send_analyzed_news(analyzed_article)
                        
                        self.processed_count += len(analyzed)
                        
                        logger.info(
                            f"Processed batch: {len(analyzed)}/{len(batch)} articles"
                        )
                        
                        # 배치 초기화
                        batch = []
                        last_flush = current_time
                
                except Exception as e:
                    logger.error(f"Error processing news: {e}")
                    self.error_count += 1
        
        @self.app.timer(interval=30.0)
        async def log_metrics():
            """메트릭 로깅 (30초마다)"""
            logger.info(
                f"Metrics: processed={self.processed_count}, "
                f"errors={self.error_count}"
            )
    
    async def _send_analyzed_news(self, article: AnalyzedNewsArticle):
        """분석된 뉴스를 output topic으로 전송"""
        import json
        
        # Pydantic 모델을 JSON으로 직렬화
        data = article.model_dump_json()
        
        # Kafka로 전송
        await self.output_topic.send(value=data.encode('utf-8'))
    
    def run(self):
        """스트림 프로세서 실행"""
        logger.info("Starting NewsStreamProcessor...")
        self.app.main()
    
    async def stop(self):
        """스트림 프로세서 종료"""
        await self.inference_engine.close()
        logger.info("NewsStreamProcessor stopped")


# CLI 진입점
if __name__ == "__main__":
    import os
    
    processor = NewsStreamProcessor(
        broker=os.getenv("KAFKA_BROKER", "kafka://localhost:9092"),
        input_topic=os.getenv("INPUT_TOPIC", "news_stream"),
        output_topic=os.getenv("OUTPUT_TOPIC", "analyzed_news"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )
    
    processor.run()
