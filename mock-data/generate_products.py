import json
import random
from datetime import datetime, timedelta
from kafka import KafkaProducer

# 品类列表
CATEGORIES = ["手机", "电脑", "服装", "美妆", "食品", "家居", "数码", "运动"]

# 商品名称模板
PRODUCT_NAMES = {
    "手机": ["iPhone 15 Pro", "华为Mate 60", "小米14", "OPPO Find X7", "vivo X100"],
    "电脑": ["MacBook Pro", "联想小新", "华为MateBook", "戴尔XPS", "华硕天选"],
    "服装": ["潮流卫衣", "时尚连衣裙", "休闲裤", "羽绒服", "T恤"],
    "美妆": ["口红", "粉底液", "眼影盘", "面膜", "精华液"],
    "食品": ["零食大礼包", "坚果", "巧克力", "饼干", "果干"],
    "家居": ["智能台灯", "收纳箱", "抱枕", "香薰", "花瓶"],
    "数码": ["蓝牙耳机", "充电宝", "键盘", "鼠标", "摄像头"],
    "运动": ["运动鞋", "瑜伽垫", "跑步机", "哑铃", "运动服"]
}

def generate_product(product_id: int, category: str) -> dict:
    """生成单个商品数据"""
    name = random.choice(PRODUCT_NAMES[category])
    price = round(random.uniform(10, 5000), 2)
    sales = random.randint(100, 100000)
    rating = round(random.uniform(3.5, 5.0), 1)

    # 爆款指数 = 销量 * 好评率 * 随机权重
    hot_score = round(sales * (rating / 5) * random.uniform(0.8, 1.2), 2)

    return {
        "product_id": f"P{product_id:06d}",
        "name": f"{name} {random.choice(['Pro', 'Max', 'Plus', 'Edition'])}",
        "category": category,
        "price": price,
        "sales": sales,
        "rating": rating,
        "hot_score": hot_score,
        "image_url": f"https://example.com/images/P{product_id:06d}.jpg",
        "description": f"这是一款优质的{category}产品",
        "create_time": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat()
    }

def generate_products(count: int = 100) -> list:
    """生成商品数据列表"""
    products = []
    for i in range(count):
        category = random.choice(CATEGORIES)
        product = generate_product(i + 1, category)
        products.append(product)
    return products

def send_to_kafka(products: list):
    """发送数据到Kafka"""
    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8')
    )

    topic = 'products'
    for product in products:
        producer.send(topic, value=product)
        print(f"发送商品: {product['product_id']} - {product['name']}")

    producer.flush()
    print(f"共发送 {len(products)} 条商品数据")

if __name__ == "__main__":
    products = generate_products(100)

    # 保存到文件
    with open('products.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    print(f"生成 {len(products)} 条商品数据")

    # 发送到Kafka
    try:
        send_to_kafka(products)
    except Exception as e:
        print(f"Kafka发送失败: {e}")
        print("数据已保存到 products.json")
