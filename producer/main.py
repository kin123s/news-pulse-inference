"""
FastAPI Producer Server
Fetches news from external API and sends to Kafka
"""
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

from config import get_settings
from kafka_producer import NewsKafkaProducer
from news_client import NewsAPIClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
news_fetched_total = Counter('news_fetched_total', 'Total number of news articles fetched')
news_sent_total = Counter('news_sent_total', 'Total number of news articles sent to Kafka')
news_fetch_duration = Histogram('news_fetch_duration_seconds', 'Time spent fetching news')

settings = get_settings()
kafka_producer = None
news_client = None
fetch_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    global kafka_producer, news_client, fetch_task
    
    # Startup
    logger.info("Starting Producer service...")
    kafka_producer = NewsKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        topic=settings.kafka_topic
    )
    news_client = NewsAPIClient(
        api_key=settings.news_api_key,
        api_url=settings.news_api_url
    )
    
    # Start background task for continuous news fetching
    fetch_task = asyncio.create_task(fetch_news_continuously())
    
    yield
    
    # Shutdown
    logger.info("Shutting down Producer service...")
    if fetch_task:
        fetch_task.cancel()
    if kafka_producer:
        kafka_producer.close()
    if news_client:
        await news_client.close()


app = FastAPI(
    title="News Producer API",
    description="Fetches news from external API and sends to Kafka stream",
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


async def fetch_news_continuously():
    """Background task to continuously fetch news"""
    while True:
        try:
            logger.info("Fetching news from API...")
            with news_fetch_duration.time():
                articles = await news_client.fetch_news()
            
            news_fetched_total.inc(len(articles))
            
            for article in articles:
                success = kafka_producer.send_news(article)
                if success:
                    news_sent_total.inc()
            
            logger.info(f"Sent {len(articles)} articles to Kafka")
            
            # Wait 5 minutes before next fetch
            await asyncio.sleep(300)
            
        except asyncio.CancelledError:
            logger.info("Fetch task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in fetch loop: {e}")
            await asyncio.sleep(60)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "news-producer",
        "status": "running",
        "kafka_topic": settings.kafka_topic
    }


@app.post("/fetch-now")
async def fetch_now(background_tasks: BackgroundTasks):
    """Trigger immediate news fetch"""
    async def fetch_and_send():
        articles = await news_client.fetch_news()
        news_fetched_total.inc(len(articles))
        
        sent_count = 0
        for article in articles:
            success = kafka_producer.send_news(article)
            if success:
                sent_count += 1
                news_sent_total.inc()
        
        logger.info(f"Manual fetch: sent {sent_count}/{len(articles)} articles")
    
    background_tasks.add_task(fetch_and_send)
    return {"message": "Fetching news in background"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.producer_port)
