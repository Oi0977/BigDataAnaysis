"""
生成商品基础信息（模拟从抖音平台爬取的原始数据）

输出字段: product_id, name, category, brand, price, original_price,
         image_url, description, shop_name, create_time

不包含计算指标（hot_score, sales, rating 等由 Spark 负责）
"""

import json
import os
import random
from datetime import datetime, timedelta

# ============================================================
# 品类 → 品牌映射
# ============================================================
CATEGORIES = {
    "手机": ["苹果", "华为", "小米", "OPPO", "vivo", "荣耀"],
    "电脑": ["苹果", "联想", "华为", "戴尔", "华硕"],
    "服装": ["优衣库", "ZARA", "太平鸟", "UR", "森马"],
    "美妆": ["完美日记", "花西子", "兰蔻", "雅诗兰黛", "MAC"],
    "食品": ["三只松鼠", "良品铺子", "百草味", "来伊份"],
    "家居": ["宜家", "无印良品", "网易严选", "名创优品"],
    "数码": ["索尼", "BOSE", "苹果", "漫步者", "小米"],
    "运动": ["耐克", "阿迪达斯", "李宁", "安踏", "匹克"],
}

# ============================================================
# 品类 → 商品名列表（品牌前缀 + 基础名）
# ============================================================
PRODUCT_NAMES = {
    "手机": ["Mate 60", "Find X7", "小米14", "iPhone 15", "X100", "Magic6"],
    "电脑": ["MateBook Pro", "小新Pro", "MacBook Air", "XPS 13", "天选Pro"],
    "服装": ["连衣裙", "卫衣", "休闲裤", "羽绒服", "T恤"],
    "美妆": ["口红", "粉底液", "眼影盘", "面膜", "精华液"],
    "食品": ["坚果礼盒", "牛肉干", "曲奇饼干", "果干", "辣条"],
    "家居": ["台灯", "收纳箱", "抱枕", "香薰", "花瓶"],
    "数码": ["蓝牙耳机", "充电宝", "机械键盘", "鼠标", "摄像头"],
    "运动": ["运动鞋", "瑜伽垫", "跑步机", "哑铃", "运动服"],
}

# ============================================================
# 品类 → 价格区间 [min, max]
# ============================================================
PRICE_RANGES = {
    "手机": [1000, 8000],
    "电脑": [3000, 12000],
    "服装": [50, 800],
    "美妆": [50, 600],
    "食品": [20, 300],
    "家居": [30, 500],
    "数码": [50, 3000],
    "运动": [100, 2000],
}

# ============================================================
# 品类 → 特征词（用于描述模板占位符 {feature}）
# ============================================================
CATEGORY_FEATURES = {
    "手机": ["拍照", "续航", "性能", "屏幕", "快充", "信号"],
    "电脑": ["性能", "续航", "屏幕", "散热", "接口", "便携"],
    "服装": ["面料", "剪裁", "版型", "做工", "设计感", "舒适度"],
    "美妆": ["持妆力", "显色度", "肤感", "成分", "质感", "保湿度"],
    "食品": ["口感", "新鲜度", "包装", "分量", "口味", "品质"],
    "家居": ["材质", "设计", "耐用性", "实用性", "颜值", "工艺"],
    "数码": ["音质", "延迟", "续航", "连接稳定性", "佩戴感", "降噪"],
    "运动": ["缓震", "透气性", "耐磨性", "弹性", "支撑性", "重量"],
}

# ============================================================
# 价格区间描述词
# ============================================================
def get_price_desc(price: float) -> str:
    """根据价格返回对应的描述词"""
    if price < 100:
        return "百元以内"
    elif price < 500:
        return "平价好物"
    elif price < 2000:
        return "千元档"
    elif price < 5000:
        return "高端旗舰"
    else:
        return "顶级奢华"


# ============================================================
# 加载描述模板
# ============================================================
def load_templates() -> dict:
    """
    从 mock-data/templates/product_templates.json 加载描述模板。
    如果文件不存在或读取失败，返回空字典（使用默认描述）。
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(script_dir, "templates", "product_templates.json")
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"警告：无法加载描述模板 ({e})，将使用默认描述")
        return {}


# ============================================================
# 生成描述文本
# ============================================================
def generate_description(
    templates: dict, category: str, brand: str, price: float
) -> str:
    """
    根据模板生成商品描述，替换占位符:
    - {brand}    → 品牌名
    - {price_desc} → 价格区间描述词
    - {feature}  → 品类特征词
    """
    if templates and category in templates:
        template = random.choice(templates[category])
        feature = random.choice(CATEGORY_FEATURES[category])
        return template.format(
            brand=brand,
            price_desc=get_price_desc(price),
            feature=feature,
        )
    # 默认描述
    return f"这是一款优质的{category}产品，来自{brand}品牌"


# ============================================================
# 生成店铺名称
# ============================================================
def generate_shop_name(brand: str, category: str) -> str:
    """店铺名称: "{brand}{品类}旗舰店" 或 "{brand}官方旗舰店" """
    if random.random() < 0.5:
        return f"{brand}{category}旗舰店"
    return f"{brand}官方旗舰店"


# ============================================================
# 生成单个商品
# ============================================================
def generate_product(product_id: int, templates: dict) -> dict:
    """
    生成一条商品基础信息。
    - product_id: 从 1 开始的序号，格式为 P000001
    - templates: 描述模板字典
    """
    # 均匀分配品类（调用方保证）
    category = _current_category

    # 随机选品牌和商品名
    brand = random.choice(CATEGORIES[category])
    product_name = random.choice(PRODUCT_NAMES[category])
    name = f"{brand} {product_name}"

    # 价格
    min_price, max_price = PRICE_RANGES[category]
    price = round(random.uniform(min_price, max_price), 2)

    # 原价 = price * (1 + 10%~50%)，向上取整到整数
    markup = random.uniform(1.10, 1.50)
    original_price = round(price * markup, 2)

    # 上架时间（最近 365 天内随机）
    days_ago = random.randint(0, 365)
    create_time = (datetime.now() - timedelta(days=days_ago)).strftime(
        "%Y-%m-%dT%H:%M:%S"
    )

    # 描述
    description = generate_description(templates, category, brand, price)

    # 店铺名
    shop_name = generate_shop_name(brand, category)

    return {
        "product_id": f"P{product_id:06d}",
        "name": name,
        "category": category,
        "brand": brand,
        "price": price,
        "original_price": original_price,
        "image_url": "",  # 暂时为空
        "description": description,
        "shop_name": shop_name,
        "create_time": create_time,
    }


# ============================================================
# 生成全部商品（8 个品类均匀分布）
# ============================================================
_current_category = ""  # 供 generate_product 使用的全局变量


def generate_products(count: int = 100) -> list:
    """
    生成 count 个商品，8 个品类大致均匀分布。
    多出的余数随机分配给部分品类。
    """
    global _current_category

    templates = load_templates()
    categories = list(CATEGORIES.keys())

    # 计算每个品类的数量
    base_count = count // len(categories)  # 100 // 8 = 12
    remainder = count % len(categories)    # 100 % 8 = 4
    category_counts = {}
    for cat in categories:
        category_counts[cat] = base_count
    # 余数随机分配
    extra_cats = random.sample(categories, remainder)
    for cat in extra_cats:
        category_counts[cat] += 1

    products = []
    pid = 1
    for category in categories:
        _current_category = category
        for _ in range(category_counts[category]):
            products.append(generate_product(pid, templates))
            pid += 1

    return products


# ============================================================
# 发送到 Kafka
# ============================================================
def send_to_kafka(products: list, bootstrap_servers: str = "localhost:9094"):
    """
    将商品数据发送到 Kafka topic: raw_products。
    Kafka 不可用时抛出异常，由调用方处理。
    """
    from confluent_kafka import Producer

    topic = "raw_products"

    def delivery_callback(err, msg):
        if err:
            print(f"  [失败] {msg.key().decode()}: {err}")
        else:
            print(f"  [成功] {msg.key().decode()} -> {msg.topic()}[{msg.partition()}]")

    producer = Producer({
        "bootstrap.servers": bootstrap_servers,
        "client.id": "mock-product-generator",
    })

    success_count = 0
    fail_count = 0

    for product in products:
        value = json.dumps(product, ensure_ascii=False).encode("utf-8")
        try:
            producer.produce(
                topic,
                key=product["product_id"],
                value=value,
                callback=delivery_callback,
            )
            success_count += 1
        except Exception as e:
            fail_count += 1
            print(f"  [排队失败] {product['product_id']}: {e}")

    producer.flush(timeout=10)
    print(f"Kafka 发送完成: 成功 {success_count}, 失败 {fail_count}, 共 {len(products)} 条")


# ============================================================
# 读取 backend/.env 中的 Kafka 配置
# ============================================================
def load_kafka_config() -> str:
    """
    从 backend/.env 读取 KAFKA_BOOTSTRAP_SERVERS 配置。
    如果读取失败，使用默认值 localhost:9094。
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, "..", "backend", ".env")
    default_server = "localhost:9094"

    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("KAFKA_BOOTSTRAP_SERVERS="):
                    return line.split("=", 1)[1]
    except FileNotFoundError:
        pass

    return default_server


# ============================================================
# 主入口
# ============================================================
if __name__ == "__main__":
    # 生成 2000 个商品
    products = generate_products(2000)

    # 保存到 JSON 文件
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, "products.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    print(f"已生成 {len(products)} 条商品数据 -> {output_file}")

    # 发送到 Kafka（失败不影响 JSON 文件）
    try:
        bootstrap_servers = load_kafka_config()
        print(f"正在发送到 Kafka ({bootstrap_servers}) topic: raw_products ...")
        send_to_kafka(products, bootstrap_servers)
    except Exception as e:
        print(f"Kafka 发送失败: {e}")
        print("数据已保存到 products.json，可稍后重试发送")
