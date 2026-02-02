"""
FastAPI Consumer Server
Consumes news from Kafka, analyzes, stores in Redis, and streams via WebSocket
"""
import logging
import asyncio
import json
from contextlib import asynccontextmanager
from typing import Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

from config import get_settings
from kafka_consumer import NewsKafkaConsumer
from analyzer import NewsAnalyzer
from redis_storage import RedisStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
news_consumed_total = Counter('news_consumed_total', 'Total number of news articles consumed')
news_analyzed_total = Counter('news_analyzed_total', 'Total number of news articles analyzed')
news_stored_total = Counter('news_stored_total', 'Total number of news articles stored')
analysis_duration = Histogram('news_analysis_duration_seconds', 'Time spent analyzing news')
active_websocket_connections = Gauge('active_websocket_connections', 'Number of active WebSocket connections')

settings = get_settings()
kafka_consumer = None
analyzer = None
redis_storage = None
consumer_task = None

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        active_websocket_connections.set(len(self.active_connections))
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        active_websocket_connections.set(len(self.active_connections))
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    global kafka_consumer, analyzer, redis_storage, consumer_task
    
    # Startup
    logger.info("Starting Consumer service...")
    analyzer = NewsAnalyzer()
    redis_storage = RedisStorage(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db
    )
    
    # Start Kafka consumer in background thread
    consumer_task = asyncio.create_task(start_kafka_consumer())
    
    yield
    
    # Shutdown
    logger.info("Shutting down Consumer service...")
    if consumer_task:
        consumer_task.cancel()
    if redis_storage:
        redis_storage.close()


app = FastAPI(
    title="News Consumer API",
    description="Consumes news from Kafka, analyzes, and provides WebSocket streaming",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def process_news(news_data: dict):
    """Process news message from Kafka"""
    try:
        news_consumed_total.inc()
        
        # Analyze the news
        with analysis_duration.time():
            analyzed_data = analyzer.analyze(news_data)
        news_analyzed_total.inc()
        
        # Store in Redis
        news_id = analyzed_data.get('id')
        if redis_storage.store_analysis(news_id, analyzed_data):
            news_stored_total.inc()
        
        # Broadcast to WebSocket clients
        asyncio.create_task(manager.broadcast({
            "type": "new_analysis",
            "data": analyzed_data
        }))
        
    except Exception as e:
        logger.error(f"Error processing news: {e}")


async def start_kafka_consumer():
    """Start Kafka consumer in background"""
    global kafka_consumer
    
    try:
        kafka_consumer = NewsKafkaConsumer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            topic=settings.kafka_topic,
            group_id=settings.kafka_group_id
        )
        
        # Run consumer in thread pool to avoid blocking
        await asyncio.get_event_loop().run_in_executor(
            None, kafka_consumer.consume_messages, process_news
        )
    except asyncio.CancelledError:
        logger.info("Kafka consumer task cancelled")
    except Exception as e:
        logger.error(f"Error in Kafka consumer: {e}")


@app.get("/")
async def root():
    """Health check endpoint"""
    stats = redis_storage.get_stats() if redis_storage else {}
    return {
        "service": "news-consumer",
        "status": "running",
        "kafka_topic": settings.kafka_topic,
        "stats": stats
    }


@app.get("/news/recent")
async def get_recent_news(limit: int = 20):
    """Get recent analyzed news"""
    news = redis_storage.get_recent_news(limit)
    return {"count": len(news), "news": news}


@app.get("/news/top")
async def get_top_news(limit: int = 10):
    """Get top news by importance"""
    news = redis_storage.get_top_news(limit)
    return {"count": len(news), "news": news}


@app.get("/news/{news_id}")
async def get_news(news_id: str):
    """Get specific news analysis"""
    analysis = redis_storage.get_analysis(news_id)
    if analysis:
        return analysis
    return {"error": "News not found"}, 404


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time news feed"""
    await manager.connect(websocket)
    
    try:
        # Send initial data
        recent_news = redis_storage.get_recent_news(10)
        await websocket.send_json({
            "type": "initial_data",
            "data": recent_news
        })
        
        # Keep connection alive
        while True:
            # Wait for client messages (ping/pong)
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.consumer_port)
