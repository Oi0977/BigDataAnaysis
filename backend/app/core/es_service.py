import threading
from elasticsearch import Elasticsearch
from typing import List, Dict, Any, Optional
from app.config import settings

class ESService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.client = None
        self.index_name = settings.elasticsearch_index_products
        self.connect()
        self._initialized = True

    def connect(self):
        """连接Elasticsearch"""
        try:
            self.client = Elasticsearch(
                f"http://{settings.elasticsearch_host}"
            )
            print("Elasticsearch连接成功")
        except Exception as e:
            print(f"Elasticsearch连接失败: {e}")

    def create_index(self):
        """创建索引"""
        try:
            if not self.client.indices.exists(index=self.index_name):
                mapping = {
                    "mappings": {
                        "properties": {
                            "productId": {"type": "keyword"},
                            "name": {"type": "text", "analyzer": "ik_max_word"},
                            "category": {"type": "keyword"},
                            "description": {"type": "text", "analyzer": "ik_max_word"},
                            "hotScore": {"type": "float"},
                            "sales": {"type": "long"},
                            "price": {"type": "float"}
                        }
                    }
                }
                self.client.indices.create(index=self.index_name, body=mapping)
                print(f"创建索引: {self.index_name}")
        except Exception as e:
            print(f"创建索引失败: {e}")

    def index_product(self, product: Dict[str, Any]):
        """索引商品数据"""
        try:
            doc = {
                "productId": product['product_id'],
                "name": product['name'],
                "category": product['category'],
                "description": product.get('description', ''),
                "hotScore": product['hot_score'],
                "sales": product['sales'],
                "price": product['price']
            }

            self.client.index(
                index=self.index_name,
                id=product['product_id'],
                document=doc
            )
        except Exception as e:
            print(f"索引商品失败: {e}")

    def search_products(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """搜索商品"""
        try:
            search_query = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["name^3", "description^2", "category"]
                    }
                },
                "size": limit,
                "sort": [{"_score": "desc"}, {"hotScore": "desc"}]
            }

            response = self.client.search(
                index=self.index_name,
                body=search_query
            )

            products = []
            for hit in response['hits']['hits']:
                product = hit['_source']
                product['score'] = hit['_score']
                products.append(product)

            return products
        except Exception as e:
            print(f"搜索商品失败: {e}")
            return []

    def get_similar_products(self, product_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """获取相似商品"""
        try:
            # 先获取商品信息
            product = self.client.get(
                index=self.index_name,
                id=product_id
            )['_source']

            # 用商品名称和描述搜索相似商品
            similar_query = {
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"name": product['name']}},
                            {"match": {"description": product.get('description', '')}}
                        ],
                        "must_not": [
                            {"term": {"productId": product_id}}
                        ]
                    }
                },
                "size": limit
            }

            response = self.client.search(
                index=self.index_name,
                body=similar_query
            )

            return [hit['_source'] for hit in response['hits']['hits']]
        except Exception as e:
            print(f"获取相似商品失败: {e}")
            return []

# 模块级别获取单例实例
es_service = ESService()
