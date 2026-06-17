"""
Kafka 消费者脚本
从 Kafka 消费商品和评价数据，写入 HBase 和 Elasticsearch

使用方式:
    在 PyCharm 中直接运行此文件
    或 cd 项目根目录后: python scripts/kafka_consumer.py
"""
import json
import os
import signal
import sys

# 将项目根目录加入 sys.path（兼容所有运行方式）
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from confluent_kafka import Consumer, KafkaError
from backend.app.config import settings
from backend.app.core.hbase_service import hbase_service
from backend.app.core.es_service import es_service


def product_callback(data: dict):
    """处理商品消息"""
    try:
        hbase_service.insert_product(data)
        es_service.index_product(data)
        print(f"商品写入成功: {data.get('product_id')}")
    except Exception as e:
        print(f"商品写入失败: {e}")


def review_callback(data: dict):
    """处理评价消息"""
    try:
        hbase_service.insert_review(data)
        print(f"评价写入成功: {data.get('review_id')}")
    except Exception as e:
        print(f"评价写入失败: {e}")


def create_consumer(topic: str, callback, group_id: str = "douyin-consumer"):
    """创建并启动消费者"""
    consumer = Consumer({
        'bootstrap.servers': settings.kafka_bootstrap_servers,
        'group.id': group_id,
        'auto.offset.reset': 'earliest'
    })
    consumer.subscribe([topic])
    return consumer, callback


def main():
    print("=" * 50)
    print("Kafka 消费者启动")
    print("=" * 50)
    print(f"Kafka 服务器: {settings.kafka_bootstrap_servers}")
    print(f"商品 Topic: {settings.kafka_topic_products}")
    print(f"评价 Topic: {settings.kafka_topic_reviews}")

    # 创建消费者
    product_consumer, product_cb = create_consumer(
        settings.kafka_topic_products,
        product_callback,
        "douyin-product-group"
    )
    review_consumer, review_cb = create_consumer(
        settings.kafka_topic_reviews,
        review_callback,
        "douyin-review-group"
    )

    running = True

    def signal_handler(sig, frame):
        nonlocal running
        print("\n正在停止消费者...")
        running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("\n等待消息中... (Ctrl+C 停止)")

    try:
        while running:
            # 消费商品消息
            msg = product_consumer.poll(1.0)
            if msg is not None and not msg.error():
                try:
                    data = json.loads(msg.value().decode('utf-8'))
                    product_cb(data)
                except Exception as e:
                    print(f"处理商品消息失败: {e}")
            elif msg is not None and msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    print(f"商品消费者错误: {msg.error()}")

            # 消费评价消息
            msg = review_consumer.poll(1.0)
            if msg is not None and not msg.error():
                try:
                    data = json.loads(msg.value().decode('utf-8'))
                    review_cb(data)
                except Exception as e:
                    print(f"处理评价消息失败: {e}")
            elif msg is not None and msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    print(f"评价消费者错误: {msg.error()}")

    finally:
        product_consumer.close()
        review_consumer.close()
        print("消费者已停止")


if __name__ == "__main__":
    main()
