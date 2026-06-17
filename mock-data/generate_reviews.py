#!/usr/bin/env python3
"""
评价数据生成器
为每个商品生成8-15条评价，使用NLP引擎从模板库生成真实文本。
好评60% + 中评20% + 差评20%。

运行方式:
    cd 项目根目录
    uv run python mock-data/generate_reviews.py
"""

import json
import os
import random
import sys
from datetime import datetime, timedelta

# 将项目根目录加入sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 导入NLP生成器
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nlp_generator import NLPGenerator

# 配置
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PRODUCTS_FILE = os.path.join(SCRIPT_DIR, "products.json")
TEMPLATES_DIR = os.path.join(SCRIPT_DIR, "templates")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "reviews.json")

# 评价用户名模板
USERNAMES = [
    "小明", "小红", "小李", "小王", "小张", "小刘", "小陈", "小杨",
    "小赵", "小黄", "小周", "小吴", "小徐", "小孙", "小马", "小朱",
    "快乐买家", "精致生活", "爱购物", "理性消费", "品质生活", "实用主义",
    "追风少年", "月下独酌", "清风徐来", "星辰大海", "一叶知秋", "静水流深"
]


def load_products() -> list:
    """加载商品数据"""
    if not os.path.exists(PRODUCTS_FILE):
        print(f"[错误] 商品文件不存在: {PRODUCTS_FILE}")
        print("请先运行 generate_products.py")
        sys.exit(1)

    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_review_time(create_time_str: str) -> str:
    """在商品上架时间之后随机生成评价时间"""
    try:
        create_time = datetime.fromisoformat(create_time_str)
    except (ValueError, TypeError):
        create_time = datetime.now() - timedelta(days=180)

    # 在上架后30天到至今之间随机
    now = datetime.now()
    max_days = (now - create_time).days
    if max_days <= 0:
        max_days = 30

    random_days = random.randint(1, max(max_days, 1))
    random_hours = random.randint(8, 23)
    random_minutes = random.randint(0, 59)

    review_time = create_time + timedelta(days=random_days, hours=random_hours, minutes=random_minutes)
    if review_time > now:
        review_time = now - timedelta(days=random.randint(0, 7))

    return review_time.isoformat()


def generate_reviews_for_product(product: dict, nlp_gen: NLPGenerator, review_count: int = None) -> list:
    """为单个商品生成评价列表"""
    product_id = product["product_id"]
    category = product["category"]
    brand = product.get("brand", "")
    price = product.get("price", 100)
    create_time = product.get("create_time", datetime.now().isoformat())

    # 随机评价数量 8-15条
    if review_count is None:
        review_count = random.randint(8, 15)

    reviews = []
    for i in range(review_count):
        # 按比例分配情感: 好评60%, 中评20%, 差评20%
        rand = random.random()
        if rand < 0.6:
            sentiment = "positive"
        elif rand < 0.8:
            sentiment = "neutral"
        else:
            sentiment = "negative"

        # 使用NLP引擎生成评价
        product_info = {
            "brand": brand,
            "price": price,
            "category": category
        }
        review_data = nlp_gen.generate_review(category, sentiment, product_info)

        # 生成评价时间
        review_time = generate_review_time(create_time)

        # 随机点赞数
        if sentiment == "positive":
            likes = random.randint(0, 50)
        elif sentiment == "neutral":
            likes = random.randint(0, 15)
        else:
            likes = random.randint(0, 30)

        review = {
            "review_id": f"R{product_id[1:]}_{i+1:03d}",
            "product_id": product_id,
            "content": review_data["content"],
            "rating": review_data["rating"],
            "sentiment": sentiment,
            "likes": likes,
            "username": random.choice(USERNAMES),
            "create_time": review_time
        }
        reviews.append(review)

    return reviews


def main():
    """主入口"""
    print("=" * 60)
    print("评价数据生成器")
    print(f"商品文件: {PRODUCTS_FILE}")
    print(f"模板目录: {TEMPLATES_DIR}")
    print(f"输出文件: {OUTPUT_FILE}")
    print("=" * 60)

    # 加载商品数据
    products = load_products()
    print(f"[成功] 加载 {len(products)} 个商品")

    # 初始化NLP生成器
    nlp_gen = NLPGenerator(templates_dir=TEMPLATES_DIR)
    print(f"[成功] NLP生成器初始化完成")

    # 为每个商品生成评价
    all_reviews = []
    for i, product in enumerate(products):
        reviews = generate_reviews_for_product(product, nlp_gen)
        all_reviews.extend(reviews)

        if (i + 1) % 20 == 0:
            print(f"  进度: {i+1}/{len(products)} 商品，已生成 {len(all_reviews)} 条评价")

    # 统计
    positive_count = sum(1 for r in all_reviews if r["sentiment"] == "positive")
    neutral_count = sum(1 for r in all_reviews if r["sentiment"] == "neutral")
    negative_count = sum(1 for r in all_reviews if r["sentiment"] == "negative")
    total = len(all_reviews)

    print(f"\n[完成] 共生成 {total} 条评价")
    print(f"  好评: {positive_count} ({positive_count/total*100:.1f}%)")
    print(f"  中评: {neutral_count} ({neutral_count/total*100:.1f}%)")
    print(f"  差评: {negative_count} ({negative_count/total*100:.1f}%)")

    # 保存到文件
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_reviews, f, ensure_ascii=False, indent=2)
    print(f"[成功] 保存到 {OUTPUT_FILE}")

    # 尝试发送到Kafka
    try:
        from confluent_kafka import Producer

        producer = Producer({
            'bootstrap.servers': 'localhost:9094'
        })

        topic = 'raw_reviews'
        sent_count = 0
        for review in all_reviews:
            value = json.dumps(review, ensure_ascii=False).encode('utf-8')
            producer.produce(topic, key=review['review_id'], value=value)
            sent_count += 1

        producer.flush()
        print(f"[成功] 发送 {sent_count} 条评价到Kafka topic: {topic}")
    except Exception as e:
        print(f"[跳过] Kafka发送失败: {e}")
        print("  数据已保存到JSON文件")


if __name__ == "__main__":
    main()
