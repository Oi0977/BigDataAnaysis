.PHONY: help build up down logs test mock-data init-data full-init kafka-consumer spark-clean spark-hot spark-nlp

help: ## 显示帮助信息
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## 构建Docker镜像
	docker-compose build

up: ## 启动所有服务
	docker-compose up -d

down: ## 停止所有服务
	docker-compose down

logs: ## 查看日志
	docker-compose logs -f

test: ## 运行测试
	cd backend && uv run pytest tests/ -v

mock-data: ## 生成Mock数据
	cd mock-data && uv run python generate_products.py && uv run python generate_reviews.py

init-data: ## 初始化数据到HBase和ES
	cd backend && uv run python ../scripts/init_data.py

full-init: mock-data init-data ## 完整初始化（生成数据+灌入存储）

kafka-consumer: ## 启动Kafka消费者
	cd backend && uv run python ../scripts/kafka_consumer.py

spark-clean: ## 运行Spark数据清洗
	cd backend && uv run spark-submit ../spark-jobs/data_cleaning.py

spark-hot: ## 运行Spark热度评分
	cd backend && uv run spark-submit ../spark-jobs/hot_score.py

spark-nlp: ## 运行Spark NLP分析
	cd backend && uv run spark-submit ../spark-jobs/nlp_analysis.py

# 启动大数据组件（不包含前后端）
up-bigdata: ## 启动大数据组件
	docker-compose up -d kafka spark-master spark-worker hdfs-namenode hdfs-datanode hbase-master hbase-regionserver zookeeper elasticsearch

# 启动全部Docker服务
up-all: ## 启动全部Docker服务
	docker-compose up -d
