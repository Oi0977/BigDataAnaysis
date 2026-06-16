from pydantic_settings import BaseSettings
from typing import Optional

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
    ai_api_url: str = "https://api.openai.com/v1/chat/completions"
    ai_model: str = "gpt-3.5-turbo"

    class Config:
        env_file = ".env"

settings = Settings()

# 根据运行模式动态调整配置
if settings.run_mode == "local":
    # 混合模式：使用localhost
    settings.kafka_bootstrap_servers = "localhost:9092"
    settings.spark_master = "spark://localhost:7077"
    settings.hbase_host = "localhost"
    settings.elasticsearch_host = "localhost:9200"
