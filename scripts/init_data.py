"""
数据初始化脚本
读取 mock-data/ 下的 JSON 文件，批量写入 HBase 和 Elasticsearch

数据流: mock JSON → HBase + ES

使用方式:
    cd 项目根目录
    uv run python scripts/init_data.py
"""
import os
import json
import sys

# 将项目根目录加入 sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 直接使用环境变量连接HBase和ES
import happybase
from elasticsearch import Elasticsearch


def get_hbase_connection():
    """获取HBase连接"""
    hbase_host = os.getenv('HBASE_HOST', 'hbase-master')
    hbase_port = int(os.getenv('HBASE_PORT', '9090'))
    return happybase.Connection(hbase_host, hbase_port)


def get_es_client():
    """获取Elasticsearch客户端"""
    es_host = os.getenv('ELASTICSEARCH_HOST', 'elasticsearch:9200')
    return Elasticsearch([f"http://{es_host}"])


def load_json_file(filename: str) -> list:
    """加载JSON文件"""
    paths = [
        os.path.join(project_root, 'mock-data', filename),
        os.path.join(project_root, filename),
    ]
    for path in paths:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    print(f"未找到文件: {filename}")
    return []


def init_hbase(products: list, reviews: list, monthly_sales: list):
    """初始化HBase数据"""
    print("\n=== 初始化 HBase ===")

    connection = get_hbase_connection()

    # 创建表
    try:
        # 检查表是否存在，如果不存在则创建
        tables = connection.tables()
        table_names = [t.decode() for t in tables]

        if 'product' not in table_names:
            connection.create_table('product', {'info': dict(max_versions=3)})
        if 'review' not in table_names:
            connection.create_table('review', {'info': dict(max_versions=3)})
        if 'monthly_sales' not in table_names:
            connection.create_table('monthly_sales', {'data': dict(max_versions=1)})

        print("表创建完成")
    except Exception as e:
        print(f"创建表失败: {e}")

    # 插入商品基础信息
    product_table = connection.table('product')
    success = fail = 0
    for product in products:
        try:
            rowkey = str(product['product_id'])
            product_table.put(rowkey.encode(), {
                'info:name': product.get('name', '').encode(),
                'info:category': product.get('category', '').encode(),
                'info:brand': product.get('brand', '').encode(),
                'info:price': str(product.get('price', 0)).encode(),
                'info:description': product.get('description', '').encode(),
                'info:shop_name': product.get('shop_name', '').encode(),
                'info:create_time': product.get('create_time', '').encode(),
            })
            success += 1
        except Exception as e:
            fail += 1
            print(f"插入商品失败 {product.get('product_id')}: {e}")
    print(f"商品插入完成: 成功 {success}, 失败 {fail}")

    # 插入评价数据
    review_table = connection.table('review')
    success = fail = 0
    for review in reviews:
        try:
            rowkey = str(review['review_id'])
            review_table.put(rowkey.encode(), {
                'info:product_id': str(review.get('product_id', '')).encode(),
                'info:content': review.get('content', '').encode(),
                'info:rating': str(review.get('rating', 0)).encode(),
                'info:create_time': review.get('create_time', '').encode(),
            })
            success += 1
        except Exception as e:
            fail += 1
            print(f"插入评价失败 {review.get('review_id')}: {e}")
    print(f"评价插入完成: 成功 {success}, 失败 {fail}")

    # 插入日销量数据（批量写入，不逐条调用）
    if monthly_sales:
        print("批量写入日销量数据...")
        sales_table = connection.table('monthly_sales')
        batch_size = 500
        success = fail = 0
        with sales_table.batch(batch_size=batch_size) as b:
            for s in monthly_sales:
                rowkey = f"{s['product_id']}_{s['date']}"
                b.put(rowkey.encode(), {
                    'data:dailySales': str(s['daily_sales']).encode(),
                    'data:dailyAmount': str(s['daily_amount']).encode(),
                })
                success += 1
        print(f"日销量批量写入完成: {success} 条（batch_size={batch_size}）")


def init_elasticsearch(products: list):
    """初始化Elasticsearch数据"""
    print("\n=== 初始化 Elasticsearch ===")

    es = get_es_client()
    index_name = "products"

    try:
        # 创建索引
        if not es.indices.exists(index=index_name):
            es.indices.create(
                index=index_name,
                body={
                    "mappings": {
                        "properties": {
                            "product_id": {"type": "keyword"},
                            "name": {"type": "text", "analyzer": "ik_max_word"},
                            "category": {"type": "keyword"},
                            "brand": {"type": "keyword"},
                            "price": {"type": "float"},
                            "description": {"type": "text", "analyzer": "ik_max_word"},
                            "shop_name": {"type": "keyword"},
                        }
                    }
                }
            )
            print("索引创建完成")
    except Exception as e:
        print(f"创建索引失败: {e}")

    success = fail = 0
    for product in products:
        try:
            doc = {
                "product_id": str(product['product_id']),
                "name": product.get('name', ''),
                "category": product.get('category', ''),
                "brand": product.get('brand', ''),
                "price": product.get('price', 0),
                "description": product.get('description', ''),
                "shop_name": product.get('shop_name', ''),
            }
            es.index(index=index_name, id=str(product['product_id']), body=doc)
            success += 1
        except Exception as e:
            fail += 1
            print(f"索引商品失败 {product.get('product_id')}: {e}")
    print(f"商品索引完成: 成功 {success}, 失败 {fail}")


def main():
    print("=" * 50)
    print("电商数据洞察平台 - 数据初始化")
    print("=" * 50)

    # 加载数据
    products = load_json_file('products.json')
    reviews = load_json_file('reviews.json')
    monthly_sales = load_json_file('monthly_sales.json')

    if not products:
        print("错误: 未找到商品数据，请先运行 mock-data 生成脚本")
        sys.exit(1)

    print(f"加载商品数据: {len(products)} 条")
    print(f"加载评价数据: {len(reviews)} 条")
    print(f"加载销量数据: {len(monthly_sales)} 条")

    has_error = False

    # 初始化 HBase
    try:
        init_hbase(products, reviews, monthly_sales)
    except Exception as e:
        print(f"HBase 初始化失败: {e}")
        print("请确保 HBase 服务已启动")
        has_error = True

    # 初始化 Elasticsearch
    try:
        init_elasticsearch(products)
    except Exception as e:
        print(f"Elasticsearch 初始化失败: {e}")
        print("请确保 Elasticsearch 服务已启动")
        has_error = True

    print("\n" + "=" * 50)
    if has_error:
        print("数据初始化完成（部分失败）")
    else:
        print("数据初始化完成!")
    print("注意: 商品分析指标(hot_score等)需要运行Spark作业后才会写入HBase")
    print("=" * 50)

    # 如果有错误，返回非零退出码
    if has_error:
        sys.exit(1)


if __name__ == "__main__":
    main()
