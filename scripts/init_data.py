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

from backend.app.core.hbase_service import hbase_service
from backend.app.core.es_service import es_service


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

    # 创建表
    try:
        hbase_service.create_tables()
        print("表创建完成")
    except Exception as e:
        print(f"创建表失败: {e}")

    # 插入商品基础信息
    success = fail = 0
    for product in products:
        try:
            hbase_service.insert_product(product)
            success += 1
        except Exception as e:
            fail += 1
            print(f"插入商品失败 {product.get('product_id')}: {e}")
    print(f"商品插入完成: 成功 {success}, 失败 {fail}")

    # 插入评价数据
    success = fail = 0
    for review in reviews:
        try:
            hbase_service.insert_review(review)
            success += 1
        except Exception as e:
            fail += 1
            print(f"插入评价失败 {review.get('review_id')}: {e}")
    print(f"评价插入完成: 成功 {success}, 失败 {fail}")

    # 插入日销量数据（批量写入，不逐条调用）
    if monthly_sales:
        print("批量写入日销量数据...")
        table = hbase_service.connection.table('monthly_sales')
        batch_size = 500
        success = fail = 0
        with table.batch(batch_size=batch_size) as b:
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

    try:
        es_service.create_index()
        print("索引创建完成")
    except Exception as e:
        print(f"创建索引失败: {e}")

    success = fail = 0
    for product in products:
        try:
            es_service.index_product(product)
            success += 1
        except Exception as e:
            fail += 1
            print(f"索引商品失败 {product.get('product_id')}: {e}")
    print(f"商品索引完成: 成功 {success}, 失败 {fail}")


def main():
    print("=" * 50)
    print("抖音电商竞品智能分析 - 数据初始化")
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

    # 初始化 HBase
    try:
        init_hbase(products, reviews, monthly_sales)
    except Exception as e:
        print(f"HBase 初始化失败: {e}")
        print("请确保 HBase 服务已启动")

    # 初始化 Elasticsearch
    try:
        init_elasticsearch(products)
    except Exception as e:
        print(f"Elasticsearch 初始化失败: {e}")
        print("请确保 Elasticsearch 服务已启动")

    print("\n" + "=" * 50)
    print("数据初始化完成!")
    print("注意: 商品分析指标(hot_score等)需要运行Spark作业后才会写入HBase")
    print("=" * 50)


if __name__ == "__main__":
    main()
