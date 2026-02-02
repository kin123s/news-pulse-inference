"""
Kafka Producer service for sending news data to Kafka stream
"""
import json
import logging
from typing import Dict, Any
from kafka import KafkaProducer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)


class NewsKafkaProducer:
    def __init__(self, bootstrap_servers: str, topic: str):
        self.topic = topic
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda v: v.encode('utf-8') if v else None,
            acks='all',
            retries=3,
            max_in_flight_requests_per_connection=1
        )
        logger.info(f"Kafka Producer initialized for topic: {topic}")
    
    def send_news(self, news_data: Dict[str, Any]) -> bool:
        """Send news data to Kafka topic"""
        try:
            # Use news ID as key for partitioning
            key = news_data.get('id', 'default')
            future = self.producer.send(self.topic, key=key, value=news_data)
            
            # Wait for the message to be sent
            record_metadata = future.get(timeout=10)
            logger.info(
                f"Sent to partition {record_metadata.partition} "
                f"at offset {record_metadata.offset}"
            )
            return True
        except KafkaError as e:
            logger.error(f"Failed to send message to Kafka: {e}")
            return False
    
    def close(self):
        """Close the producer connection"""
        self.producer.flush()
        self.producer.close()
        logger.info("Kafka Producer closed")
