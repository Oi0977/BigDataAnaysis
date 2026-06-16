import happybase
import threading
from typing import List, Dict, Any, Optional
from app.config import settings

class HBaseService:
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
        self.connection = None
        self.connect()
        self._initialized = True

    def connect(self):
        """连接HBase"""
        try:
            self.connection = happybase.Connection(
                host=settings.hbase_host,
                port=settings.hbase_port
            )
            print("HBase连接成功")
        except Exception as e:
            print(f"HBase连接失败: {e}")

    def create_tables(self):
        """创建表"""
        tables = ['product', 'review', 'copywriting']

        for table_name in tables:
            try:
                if table_name.encode() not in self.connection.tables():
                    self.connection.create_table(
                        table_name.encode(),
                        {'info': dict(max_versions=3)}
                    )
                    print(f"创建表: {table_name}")
            except Exception as e:
                print(f"创建表失败 {table_name}: {e}")

    def insert_product(self, product: Dict[str, Any]):
        """插入商品数据"""
        table = self.connection.table('product')
        table.put(
            product['product_id'].encode(),
            {
                'info:name': product['name'].encode(),
                'info:category': product['category'].encode(),
                'info:price': str(product['price']).encode(),
                'info:sales': str(product['sales']).encode(),
                'info:rating': str(product['rating']).encode(),
                'info:hotScore': str(product['hot_score']).encode(),
                'info:imageUrl': product['image_url'].encode(),
                'info:description': product.get('description', '').encode(),
                'info:createTime': product['create_time'].encode()
            }
        )

    def insert_review(self, review: Dict[str, Any]):
        """插入评价数据"""
        table = self.connection.table('review')
        table.put(
            review['review_id'].encode(),
            {
                'info:productId': review['product_id'].encode(),
                'info:content': review['content'].encode(),
                'info:rating': str(review['rating']).encode(),
                'info:keywords': ','.join(review['keywords']).encode(),
                'info:sentiment': review['sentiment'].encode(),
                'info:username': review.get('username', '').encode(),
                'info:createTime': review['create_time'].encode()
            }
        )

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """获取商品数据"""
        table = self.connection.table('product')
        row = table.row(product_id.encode())

        if not row:
            return None

        return {
            'product_id': product_id,
            'name': row.get(b'info:name', b'').decode(),
            'category': row.get(b'info:category', b'').decode(),
            'price': float(row.get(b'info:price', b'0').decode()),
            'sales': int(row.get(b'info:sales', b'0').decode()),
            'rating': float(row.get(b'info:rating', b'0').decode()),
            'hot_score': float(row.get(b'info:hotScore', b'0').decode()),
            'image_url': row.get(b'info:imageUrl', b'').decode(),
            'description': row.get(b'info:description', b'').decode(),
            'create_time': row.get(b'info:createTime', b'').decode()
        }

    def get_products_by_category(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """按品类获取商品"""
        table = self.connection.table('product')
        products = []

        for key, data in table.scan():
            if data.get(b'info:category', b'').decode() == category:
                product = {
                    'product_id': key.decode(),
                    'name': data.get(b'info:name', b'').decode(),
                    'category': category,
                    'price': float(data.get(b'info:price', b'0').decode()),
                    'sales': int(data.get(b'info:sales', b'0').decode()),
                    'rating': float(data.get(b'info:rating', b'0').decode()),
                    'hot_score': float(data.get(b'info:hotScore', b'0').decode()),
                    'image_url': data.get(b'info:imageUrl', b'').decode(),
                    'description': data.get(b'info:description', b'').decode(),
                    'create_time': data.get(b'info:createTime', b'').decode()
                }
                products.append(product)

                if len(products) >= limit:
                    break

        return sorted(products, key=lambda x: x['hot_score'], reverse=True)

    def get_reviews_by_product(self, product_id: str) -> List[Dict[str, Any]]:
        """获取商品的评价"""
        table = self.connection.table('review')
        reviews = []

        for key, data in table.scan():
            if data.get(b'info:productId', b'').decode() == product_id:
                review = {
                    'review_id': key.decode(),
                    'product_id': product_id,
                    'content': data.get(b'info:content', b'').decode(),
                    'rating': int(data.get(b'info:rating', b'0').decode()),
                    'keywords': data.get(b'info:keywords', b'').decode().split(','),
                    'sentiment': data.get(b'info:sentiment', b'').decode(),
                    'username': data.get(b'info:username', b'').decode(),
                    'create_time': data.get(b'info:createTime', b'').decode()
                }
                reviews.append(review)

        return reviews

    def close(self):
        """关闭连接"""
        if self.connection:
            self.connection.close()

# 模块级别获取单例实例
hbase_service = HBaseService()
