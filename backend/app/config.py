import os
from pydantic_settings import BaseSettings
from typing import Optional

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Settings(BaseSettings):
    # 运行模式：docker（全Docker）或 local（混合模式）
    run_mode: str = "docker"

    # Kafka配置
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_topic_products: str = "products"
    kafka_topic_reviews: str = "reviews"

    # Spark配置
    spark_master: str = "spark://spark-master:7077"
    app_name: str = "DouyinAnalytics"

    # HBase配置
    hbase_host: str = "hbase-master"
    hbase_port: int = 9090

    # Elasticsearch配置
    elasticsearch_host: str = "elasticsearch:9200"
    elasticsearch_index_products: str = "products"

    # AI服务配置
    ai_api_key: Optional[str] = None
    ai_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    ai_model: str = "qwen-plus"

    class Config:
        env_file = os.path.join(_backend_dir, ".env")

    def model_post_init(self, __context):
        if self.run_mode == "local":
            self.kafka_bootstrap_servers = "localhost:9094"
            self.spark_master = "spark://localhost:7077"
            self.hbase_host = "localhost"
            self.elasticsearch_host = "localhost:9200"

settings = Settings()
