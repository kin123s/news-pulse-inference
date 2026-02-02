"""
Kafka Consumer service for receiving news data from Kafka stream
"""
import json
import logging
from typing import Dict, Any, Callable
from kafka import KafkaConsumer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)


class NewsKafkaConsumer:
    def __init__(self, bootstrap_servers: str, topic: str, group_id: str):
        self.topic = topic
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            max_poll_records=10
        )
        logger.info(f"Kafka Consumer initialized for topic: {topic}, group: {group_id}")
    
    def consume_messages(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Consume messages from Kafka and process with callback
        
        Args:
            callback: Function to process each message
        """
        logger.info("Starting to consume messages...")
        try:
            for message in self.consumer:
                try:
                    news_data = message.value
                    logger.info(f"Received message from partition {message.partition}, offset {message.offset}")
                    callback(news_data)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        except KafkaError as e:
            logger.error(f"Kafka consumer error: {e}")
        finally:
            self.close()
    
    def close(self):
        """Close the consumer connection"""
        self.consumer.close()
        logger.info("Kafka Consumer closed")
