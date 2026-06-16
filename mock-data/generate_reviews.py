import json
import random
from datetime import datetime, timedelta
from kafka import KafkaProducer

# 差评模板
REVIEW_TEMPLATES = [
    "质量太差了，用了一天就坏了",
    "客服态度很差，问问题不回复",
    "物流太慢了，等了一周才收到",
    "和图片差距太大，实物很丑",
    "价格虚高，不值这个价",
    "包装太简陋，收到的时候已经压坏了",
    "功能不好用，操作很卡顿",
    "颜色和描述不符，色差严重",
    "尺寸不对，偏小/偏大很多",
    "噪音太大，影响使用体验",
    "续航不行，用不了多久就没电了",
    "做工粗糙，有很多线头",
    "气味很大，怀疑有甲醛",
    "安装困难，说明书不清晰",
    "售后差，退货麻烦"
]

# 关键词
KEYWORDS = {
    "质量差": ["质量", "做工", "材质", "耐用"],
    "服务差": ["客服", "售后", "态度", "回复"],
    "物流慢": ["物流", "快递", "配送", "时效"],
    "描述不符": ["图片", "实物", "颜色", "尺寸"],
    "价格高": ["价格", "值", "贵", "性价比"],
    "功能差": ["功能", "性能", "卡顿", "续航"]
}

def generate_review(review_id: int, product_id: str) -> dict:
    """生成单条差评数据"""
    content = random.choice(REVIEW_TEMPLATES)
    rating = random.randint(1, 2)  # 差评1-2星

    # 提取关键词
    keywords = []
    for category, words in KEYWORDS.items():
        if any(word in content for word in words):
            keywords.append(category)

    if not keywords:
        keywords = ["其他"]

    # 情感分析
    sentiment = "negative" if rating <= 2 else "neutral"

    return {
        "review_id": f"R{review_id:06d}",
        "product_id": product_id,
        "content": content,
        "rating": rating,
        "keywords": keywords,
        "sentiment": sentiment,
        "username": f"user_{random.randint(1000, 9999)}",
        "create_time": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
    }

def generate_reviews(product_ids: list, reviews_per_product: int = 5) -> list:
    """为每个商品生成差评数据"""
    reviews = []
    review_id = 1

    for product_id in product_ids:
        for _ in range(reviews_per_product):
            review = generate_review(review_id, product_id)
            reviews.append(review)
            review_id += 1

    return reviews

def send_to_kafka(reviews: list):
    """发送数据到Kafka"""
    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8')
    )

    topic = 'reviews'
    for review in reviews:
        producer.send(topic, value=review)
        print(f"发送评价: {review['review_id']} - {review['product_id']}")

    producer.flush()
    print(f"共发送 {len(reviews)} 条评价数据")

if __name__ == "__main__":
    # 读取商品数据
    try:
        with open('products.json', 'r', encoding='utf-8') as f:
            products = json.load(f)
        product_ids = [p['product_id'] for p in products]
    except FileNotFoundError:
        # 如果没有商品文件，生成一些测试ID
        product_ids = [f"P{i:06d}" for i in range(1, 21)]

    reviews = generate_reviews(product_ids, reviews_per_product=3)

    # 保存到文件
    with open('reviews.json', 'w', encoding='utf-8') as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)

    print(f"生成 {len(reviews)} 条差评数据")

    # 发送到Kafka
    try:
        send_to_kafka(reviews)
    except Exception as e:
        print(f"Kafka发送失败: {e}")
        print("数据已保存到 reviews.json")
