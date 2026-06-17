from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic
import json
from typing import Any
from backend.app.config import settings

class KafkaService:
    def __init__(self):
        self.producer = Producer({
            'bootstrap.servers': settings.kafka_bootstrap_servers
        })
        self.admin = AdminClient({
            'bootstrap.servers': settings.kafka_bootstrap_servers
        })

    def create_topic(self, topic: str, num_partitions: int = 3):
        """创建Topic"""
        try:
            new_topic = NewTopic(topic, num_partitions=num_partitions)
            self.admin.create_topics([new_topic])
            print(f"创建Topic: {topic}")
        except Exception as e:
            print(f"Topic已存在或创建失败: {e}")

    def send_message(self, topic: str, key: str, value: Any):
        """发送消息"""
        try:
            self.producer.produce(
                topic,
                key=key.encode('utf-8'),
                value=json.dumps(value, ensure_ascii=False).encode('utf-8')
            )
            self.producer.flush()
            return True
        except Exception as e:
            print(f"发送消息失败: {e}")
            return False

    def init_topics(self):
        """初始化所有Topic"""
        self.create_topic(settings.kafka_topic_products)
        self.create_topic(settings.kafka_topic_reviews)

kafka_service = KafkaService()
