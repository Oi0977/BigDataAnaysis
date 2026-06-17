import happybase
import json
import threading
import functools
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.app.config import settings


def _retry_on_disconnect(func):
    """装饰器：HBase连接断开时自动重连并重试，最多重试2次"""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        for attempt in range(3):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                error_msg = str(e).lower()
                is_conn_err = any(kw in error_msg for kw in [
                    'timed out', 'connection', 'broken', 'missing result',
                    'socket', 'reset', 'closed', 'eof', '10054'
                ])
                if is_conn_err and attempt < 2:
                    print(f"[HBase重试] {func.__name__} 第{attempt+1}次失败，重连中: {e}")
                    try:
                        self.connect()
                    except Exception:
                        pass
                else:
                    raise
    return wrapper


class HBaseService:
    _instance = None
    _lock = threading.Lock()

    # 新表结构定义
    TABLES = {
        'product': {'info': dict(max_versions=3)},
        'review': {'info': dict(max_versions=3)},
        'monthly_sales': {'data': dict(max_versions=1)},
        'product_analysis': {'metrics': dict(max_versions=1), 'trend': dict(max_versions=1)},
        'review_analysis': {'stats': dict(max_versions=1)},
    }

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
            if self.connection:
                try:
                    self.connection.close()
                except Exception:
                    pass
            self.connection = happybase.Connection(
                host=settings.hbase_host,
                port=settings.hbase_port,
                timeout=10
            )
            print("HBase连接成功")
        except Exception as e:
            print(f"HBase连接失败: {e}")

    def _ensure_connection(self):
        """确保连接存活，断开则自动重连"""
        try:
            self.connection.tables()
        except Exception:
            print("[HBase] 连接已断开，正在重连...")
            self.connect()
            try:
                self.connection.tables()
            except Exception as e:
                print(f"[HBase] 重连后仍无法访问: {e}")

    def create_tables(self):
        """创建所有表"""
        self._ensure_connection()
        existing = self.connection.tables()
        for table_name, families in self.TABLES.items():
            try:
                if table_name.encode() not in existing:
                    self.connection.create_table(table_name.encode(), families)
                    print(f"创建表: {table_name}")
            except Exception as e:
                print(f"创建表失败 {table_name}: {e}")

    # ==================== 商品原始数据 ====================

    @_retry_on_disconnect
    def insert_product(self, product: Dict[str, Any]):
        """插入商品基础信息"""
        table = self.connection.table('product')
        row = {
            'info:name': product['name'].encode(),
            'info:category': product['category'].encode(),
            'info:brand': product.get('brand', '').encode(),
            'info:price': str(product['price']).encode(),
            'info:originalPrice': str(product.get('original_price', 0)).encode(),
            'info:imageUrl': product.get('image_url', '').encode(),
            'info:description': product.get('description', '').encode(),
            'info:shopName': product.get('shop_name', '').encode(),
            'info:createTime': product.get('create_time', '').encode(),
        }
        table.put(product['product_id'].encode(), row)

    @_retry_on_disconnect
    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """获取商品基础信息"""
        table = self.connection.table('product')
        row = table.row(product_id.encode())
        if not row:
            return None
        return {
            'product_id': product_id,
            'name': row.get(b'info:name', b'').decode(),
            'category': row.get(b'info:category', b'').decode(),
            'brand': row.get(b'info:brand', b'').decode(),
            'price': float(row.get(b'info:price', b'0').decode()),
            'original_price': float(row.get(b'info:originalPrice', b'0').decode()),
            'image_url': row.get(b'info:imageUrl', b'').decode(),
            'description': row.get(b'info:description', b'').decode(),
            'shop_name': row.get(b'info:shopName', b'').decode(),
            'create_time': row.get(b'info:createTime', b'').decode(),
        }

    @_retry_on_disconnect
    def get_all_products(self) -> List[Dict[str, Any]]:
        """获取所有商品基础信息"""
        table = self.connection.table('product')
        products = []
        for key, data in table.scan():
            products.append({
                'product_id': key.decode(),
                'name': data.get(b'info:name', b'').decode(),
                'category': data.get(b'info:category', b'').decode(),
                'brand': data.get(b'info:brand', b'').decode(),
                'price': float(data.get(b'info:price', b'0').decode()),
                'original_price': float(data.get(b'info:originalPrice', b'0').decode()),
                'image_url': data.get(b'info:imageUrl', b'').decode(),
                'description': data.get(b'info:description', b'').decode(),
                'shop_name': data.get(b'info:shopName', b'').decode(),
                'create_time': data.get(b'info:createTime', b'').decode(),
            })
        return products

    @_retry_on_disconnect
    def get_products_by_category(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """按品类获取商品"""
        products = self.get_all_products()
        filtered = [p for p in products if p['category'] == category]
        return filtered[:limit]

    # ==================== 商品分析结果（Spark计算） ====================

    @_retry_on_disconnect
    def insert_product_analysis(self, analysis: Dict[str, Any]):
        """插入Spark计算的商品分析结果"""
        table = self.connection.table('product_analysis')
        row = {
            'metrics:hotScore': str(analysis.get('hot_score', 0)).encode(),
            'metrics:positiveRate': str(analysis.get('positive_rate', 0)).encode(),
            'metrics:negativeRate': str(analysis.get('negative_rate', 0)).encode(),
            'metrics:reviewCount': str(analysis.get('review_count', 0)).encode(),
            'metrics:avgRating': str(analysis.get('avg_rating', 0)).encode(),
            'metrics:dailyGrowth': str(analysis.get('daily_growth', 0)).encode(),
            'metrics:weeklyGrowth': str(analysis.get('weekly_growth', 0)).encode(),
            'metrics:totalSales': str(analysis.get('total_sales', 0)).encode(),
            'metrics:topTags': analysis.get('top_tags', '').encode(),
            'metrics:updateTime': datetime.now().isoformat().encode(),
        }
        breakdown = analysis.get('score_breakdown')
        if breakdown:
            row['metrics:scoreSales'] = str(breakdown.get('sales', 0)).encode()
            row['metrics:scoreGrowth'] = str(breakdown.get('growth', 0)).encode()
            row['metrics:scoreRating'] = str(breakdown.get('rating', 0)).encode()
            row['metrics:scoreReview'] = str(breakdown.get('review', 0)).encode()
        if analysis.get('sales_trend'):
            row['trend:salesTrend'] = analysis['sales_trend'].encode()
        table.put(analysis['product_id'].encode(), row)

    @_retry_on_disconnect
    def get_product_analysis(self, product_id: str) -> Optional[Dict[str, Any]]:
        """获取商品分析结果"""
        table = self.connection.table('product_analysis')
        row = table.row(product_id.encode())
        if not row:
            return None
        return {
            'product_id': product_id,
            'hot_score': float(row.get(b'metrics:hotScore', b'0').decode()),
            'positive_rate': float(row.get(b'metrics:positiveRate', b'0').decode()),
            'negative_rate': float(row.get(b'metrics:negativeRate', b'0').decode()),
            'review_count': int(row.get(b'metrics:reviewCount', b'0').decode()),
            'avg_rating': float(row.get(b'metrics:avgRating', b'0').decode()),
            'daily_growth': float(row.get(b'metrics:dailyGrowth', b'0').decode()),
            'weekly_growth': float(row.get(b'metrics:weeklyGrowth', b'0').decode()),
            'total_sales': int(row.get(b'metrics:totalSales', b'0').decode()),
            'top_tags': row.get(b'metrics:topTags', b'').decode(),
            'sales_trend': row.get(b'trend:salesTrend', b'').decode(),
            'score_breakdown': {
                'sales': float(row.get(b'metrics:scoreSales', b'0').decode()),
                'growth': float(row.get(b'metrics:scoreGrowth', b'0').decode()),
                'rating': float(row.get(b'metrics:scoreRating', b'0').decode()),
                'review': float(row.get(b'metrics:scoreReview', b'0').decode()),
            },
        }

    @_retry_on_disconnect
    def get_all_product_analysis(self) -> List[Dict[str, Any]]:
        """获取所有商品分析结果"""
        table = self.connection.table('product_analysis')
        results = []
        for key, data in table.scan():
            results.append({
                'product_id': key.decode(),
                'hot_score': float(data.get(b'metrics:hotScore', b'0').decode()),
                'positive_rate': float(data.get(b'metrics:positiveRate', b'0').decode()),
                'negative_rate': float(data.get(b'metrics:negativeRate', b'0').decode()),
                'review_count': int(data.get(b'metrics:reviewCount', b'0').decode()),
                'avg_rating': float(data.get(b'metrics:avgRating', b'0').decode()),
                'daily_growth': float(data.get(b'metrics:dailyGrowth', b'0').decode()),
                'weekly_growth': float(data.get(b'metrics:weeklyGrowth', b'0').decode()),
                'total_sales': int(data.get(b'metrics:totalSales', b'0').decode()),
                'top_tags': data.get(b'metrics:topTags', b'').decode(),
                'sales_trend': data.get(b'trend:salesTrend', b'').decode(),
                'score_breakdown': {
                    'sales': float(data.get(b'metrics:scoreSales', b'0').decode()),
                    'growth': float(data.get(b'metrics:scoreGrowth', b'0').decode()),
                    'rating': float(data.get(b'metrics:scoreRating', b'0').decode()),
                    'review': float(data.get(b'metrics:scoreReview', b'0').decode()),
                },
            })
        return results

    # ==================== 评价数据 ====================

    @_retry_on_disconnect
    def insert_review(self, review: Dict[str, Any]):
        """插入评价数据"""
        table = self.connection.table('review')
        table.put(
            review['review_id'].encode(),
            {
                'info:productId': review['product_id'].encode(),
                'info:content': review['content'].encode(),
                'info:rating': str(review['rating']).encode(),
                'info:sentiment': review.get('sentiment', '').encode(),
                'info:likes': str(review.get('likes', 0)).encode(),
                'info:username': review.get('username', '').encode(),
                'info:createTime': review.get('create_time', '').encode()
            }
        )

    @_retry_on_disconnect
    def get_reviews_by_product(self, product_id: str) -> List[Dict[str, Any]]:
        """获取商品的评价"""
        table = self.connection.table('review')
        reviews = []
        for key, data in table.scan():
            if data.get(b'info:productId', b'').decode() == product_id:
                reviews.append({
                    'review_id': key.decode(),
                    'product_id': product_id,
                    'content': data.get(b'info:content', b'').decode(),
                    'rating': int(data.get(b'info:rating', b'0').decode()),
                    'sentiment': data.get(b'info:sentiment', b'').decode(),
                    'likes': int(data.get(b'info:likes', b'0').decode()),
                    'username': data.get(b'info:username', b'').decode(),
                    'create_time': data.get(b'info:createTime', b'').decode()
                })
        return reviews

    @_retry_on_disconnect
    def get_all_reviews(self) -> List[Dict[str, Any]]:
        """获取所有评价"""
        table = self.connection.table('review')
        reviews = []
        for key, data in table.scan():
            reviews.append({
                'review_id': key.decode(),
                'product_id': data.get(b'info:productId', b'').decode(),
                'content': data.get(b'info:content', b'').decode(),
                'rating': int(data.get(b'info:rating', b'0').decode()),
                'sentiment': data.get(b'info:sentiment', b'').decode(),
                'likes': int(data.get(b'info:likes', b'0').decode()),
                'username': data.get(b'info:username', b'').decode(),
                'create_time': data.get(b'info:createTime', b'').decode()
            })
        return reviews

    # ==================== 月度销量 ====================

    @_retry_on_disconnect
    def insert_daily_sales(self, sales: Dict[str, Any]):
        """插入日销量数据"""
        table = self.connection.table('monthly_sales')
        rowkey = f"{sales['product_id']}_{sales['date']}"
        table.put(
            rowkey.encode(),
            {
                'data:dailySales': str(sales['daily_sales']).encode(),
                'data:dailyAmount': str(sales['daily_amount']).encode(),
            }
        )

    @_retry_on_disconnect
    def get_daily_sales(self, product_id: str) -> List[Dict[str, Any]]:
        """获取商品的日销量数据"""
        table = self.connection.table('monthly_sales')
        prefix = f"{product_id}_".encode()
        results = []
        for key, data in table.scan(row_prefix=prefix):
            key_str = key.decode()
            date = key_str.split('_', 1)[1] if '_' in key_str else ''
            results.append({
                'product_id': product_id,
                'date': date,
                'daily_sales': int(data.get(b'data:dailySales', b'0').decode()),
                'daily_amount': float(data.get(b'data:dailyAmount', b'0').decode()),
            })
        return results

    # ==================== 评价分析（Spark计算） ====================

    @_retry_on_disconnect
    def insert_review_analysis(self, analysis: Dict[str, Any]):
        """插入Spark计算的评价分析结果"""
        table = self.connection.table('review_analysis')
        row = {
            'stats:highFreqKeywords': analysis.get('high_freq_keywords', '').encode(),
            'stats:sentimentDistribution': analysis.get('sentiment_distribution', '').encode(),
            'stats:ratingDistribution': analysis.get('rating_distribution', '').encode(),
            'stats:updateTime': datetime.now().isoformat().encode(),
        }
        # ML分析新增字段
        for key, field in [('topicDistribution', 'topic_distribution'), ('topicKeywords', 'topic_keywords'),
                           ('clusterLabels', 'cluster_labels'), ('clusterKeywords', 'cluster_keywords'),
                           ('tfidfKeywords', 'tfidf_keywords')]:
            val = analysis.get(field, [])
            row[f'stats:{key}'] = json.dumps(val, ensure_ascii=False).encode() if val else b'[]'
        table.put(analysis['product_id'].encode(), row)

    @_retry_on_disconnect
    def get_review_analysis(self, product_id: str) -> Optional[Dict[str, Any]]:
        """获取评价分析结果"""
        table = self.connection.table('review_analysis')
        row = table.row(product_id.encode())
        if not row:
            return None
        return {
            'product_id': product_id,
            'high_freq_keywords': row.get(b'stats:highFreqKeywords', b'').decode(),
            'sentiment_distribution': row.get(b'stats:sentimentDistribution', b'').decode(),
            'rating_distribution': row.get(b'stats:ratingDistribution', b'').decode(),
            'topic_distribution': json.loads(row.get(b'stats:topicDistribution', b'[]').decode()),
            'topic_keywords': json.loads(row.get(b'stats:topicKeywords', b'[]').decode()),
            'cluster_labels': json.loads(row.get(b'stats:clusterLabels', b'{}').decode()),
            'cluster_keywords': json.loads(row.get(b'stats:clusterKeywords', b'{}').decode()),
            'tfidf_keywords': json.loads(row.get(b'stats:tfidfKeywords', b'[]').decode()),
        }

    def close(self):
        """关闭连接"""
        if self.connection:
            self.connection.close()


# 模块级别获取单例实例
hbase_service = HBaseService()
