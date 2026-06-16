.PHONY: help build up down logs test mock-data init-data

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
	cd backend && uv run python -c "from app.core.hbase_service import hbase_service; hbase_service.create_tables()"
	cd backend && uv run python -c "from app.core.es_service import es_service; es_service.create_index()"
