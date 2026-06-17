"""
月销量数据生成脚本

为每个商品生成近12个月的日销量数据，模拟每天从抖音平台采集的销量数据。
包含星期效应、月度趋势、大促活动等多种销量波动因素。
"""

import json
import math
import os
import random
from datetime import datetime, timedelta


# 大促活动配置：(名称, 月份, 日期, 前后天数, 销量倍数)
PROMOTIONS = [
    ("618大促", 6, 18, 3, (3.0, 5.0)),      # 6月18日前后3天，3-5倍
    ("双11大促", 11, 11, 3, (4.0, 6.0)),     # 11月11日前后3天，4-6倍
    ("年货节", 1, 15, 3, (2.5, 4.0)),        # 1月15日前后3天，2.5-4倍
    ("五一促销", 5, 1, 2, (2.0, 3.0)),       # 5月1日前后2天，2-3倍
]


def calculate_base_daily_sales() -> int:
    """计算基础日销量（10-500件/天）"""
    return random.randint(10, 500)


def get_weekday_factor(date: datetime) -> float:
    """
    获取星期效应因子
    周末销量比工作日高20-50%
    周一到周五: 0.8-1.0
    周六、周日: 1.2-1.5
    """
    weekday = date.weekday()  # 0=周一, 6=周日
    if weekday >= 5:  # 周末
        return random.uniform(1.2, 1.5)
    else:  # 工作日
        return random.uniform(0.8, 1.0)


def get_monthly_trend_factor(day_index: int, total_days: int, trend_type: str) -> float:
    """
    获取月度趋势因子

    参数:
        day_index: 当前是第几天（从0开始）
        total_days: 总天数
        trend_type: 趋势类型 ('up', 'down', 'stable')

    返回:
        趋势因子
    """
    progress = day_index / total_days  # 进度 0-1

    if trend_type == "up":
        # 上升趋势：月增5-15%
        monthly_growth = random.uniform(0.05, 0.15)
        months = progress * 12
        return 1 + (months * monthly_growth)
    elif trend_type == "down":
        # 下降趋势：月降3-10%
        monthly_decline = random.uniform(0.03, 0.10)
        months = progress * 12
        return 1 - (months * monthly_decline)
    else:
        # 平稳趋势：小幅波动
        return 1 + random.uniform(-0.1, 0.1)


def get_promotion_factor(date: datetime) -> float:
    """
    检查是否在大促期间，返回促销因子

    返回:
        促销因子（1.0表示无促销，其他值表示促销倍数）
    """
    for promo_name, month, day, days_before_after, multiplier_range in PROMOTIONS:
        promo_date = datetime(date.year, month, day)

        # 处理跨年情况
        if date.month < month or (date.month == month and date.day < day):
            promo_date = datetime(date.year - 1, month, day)

        diff_days = abs((date - promo_date).days)

        if diff_days <= days_before_after:
            # 在促销期间，返回随机倍数
            return random.uniform(multiplier_range[0], multiplier_range[1])

    return 1.0


def generate_daily_sales_for_product(
    product_id: str,
    price: float,
    start_date: datetime,
    total_days: int
) -> list:
    """
    为单个商品生成日销量数据

    参数:
        product_id: 商品ID
        price: 商品价格
        start_date: 开始日期
        total_days: 总天数

    返回:
        日销量数据列表
    """
    # 为每个商品确定其销量特征
    base_daily_sales = calculate_base_daily_sales()

    # 随机选择月度趋势类型
    trend_type = random.choice(["up", "down", "stable", "stable"])
    # 稳定类型权重更高（50%概率），上升和下降各25%

    # 起始销量随机波动（±20%）
    initial_variation = random.uniform(0.8, 1.2)
    base_daily_sales = int(base_daily_sales * initial_variation)

    daily_records = []

    for day_index in range(total_days):
        current_date = start_date + timedelta(days=day_index)

        # 1. 基础销量
        daily_sales = base_daily_sales

        # 2. 应用星期效应
        weekday_factor = get_weekday_factor(current_date)
        daily_sales = daily_sales * weekday_factor

        # 3. 应用月度趋势
        trend_factor = get_monthly_trend_factor(day_index, total_days, trend_type)
        daily_sales = daily_sales * trend_factor

        # 4. 应用随机波动（±30%）
        random_variation = random.uniform(0.7, 1.3)
        daily_sales = daily_sales * random_variation

        # 5. 应用大促活动
        promo_factor = get_promotion_factor(current_date)
        daily_sales = daily_sales * promo_factor

        # 确保销量为正整数，且有最小值
        daily_sales = max(1, int(daily_sales))

        # 计算当日销售额
        daily_amount = round(daily_sales * price, 2)

        record = {
            "product_id": product_id,
            "date": current_date.strftime("%Y-%m-%d"),
            "daily_sales": daily_sales,
            "daily_amount": daily_amount
        }

        daily_records.append(record)

    return daily_records


def load_products(file_path: str) -> list:
    """
    加载商品数据

    参数:
        file_path: products.json文件路径

    返回:
        商品列表

    异常:
        如果文件不存在，抛出异常
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"商品数据文件不存在: {file_path}\n"
            "请先运行 generate_products.py 生成商品数据"
        )

    with open(file_path, 'r', encoding='utf-8') as f:
        products = json.load(f)

    return products


def send_to_kafka(records: list, topic: str = "raw_monthly_sales"):
    """
    发送销量数据到Kafka

    参数:
        records: 日销量数据列表
        topic: Kafka主题名称
    """
    from confluent_kafka import Producer

    def delivery_callback(err, msg):
        if err:
            print(f"  发送失败: {err}")
        # 成功时静默处理，避免输出过多

    producer = Producer({
        'bootstrap.servers': 'localhost:9094'
    })

    # 批量发送以提高性能
    batch_size = 1000
    total_sent = 0

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]

        for record in batch:
            value = json.dumps(record, ensure_ascii=False).encode('utf-8')
            key = f"{record['product_id']}_{record['date']}"
            producer.produce(
                topic,
                key=key,
                value=value,
                callback=delivery_callback
            )
            total_sent += 1

        # 定期刷新
        if total_sent % 10000 == 0:
            producer.flush()
            print(f"  已发送 {total_sent}/{len(records)} 条记录...")

    # 最终刷新
    producer.flush()
    print(f"  Kafka发送完成，共 {total_sent} 条记录")


def save_to_json(records: list, file_path: str):
    """
    保存数据到JSON文件

    参数:
        records: 日销量数据列表
        file_path: 输出文件路径
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def print_statistics(records: list):
    """
    打印生成统计信息

    参数:
        records: 日销量数据列表
    """
    # 计算统计信息
    total_records = len(records)

    # 获取唯一商品数和日期范围
    product_ids = set(r['product_id'] for r in records)
    dates = [r['date'] for r in records]
    min_date = min(dates)
    max_date = max(dates)

    # 销量统计
    sales_values = [r['daily_sales'] for r in records]
    avg_daily_sales = sum(sales_values) / len(sales_values)
    max_daily_sales = max(sales_values)
    min_daily_sales = min(sales_values)

    # 销售额统计
    amount_values = [r['daily_amount'] for r in records]
    total_amount = sum(amount_values)
    avg_daily_amount = total_amount / len(amount_values)

    print("\n" + "=" * 60)
    print("月销量数据生成统计")
    print("=" * 60)
    print(f"商品数量: {len(product_ids)} 个")
    print(f"记录总数: {total_records:,} 条")
    print(f"日期范围: {min_date} 到 {max_date}")
    print(f"天数跨度: {(datetime.strptime(max_date, '%Y-%m-%d') - datetime.strptime(min_date, '%Y-%m-%d')).days + 1} 天")
    print("-" * 60)
    print("销量统计:")
    print(f"  平均日销量: {avg_daily_sales:.1f} 件")
    print(f"  最高日销量: {max_daily_sales} 件")
    print(f"  最低日销量: {min_daily_sales} 件")
    print("-" * 60)
    print("销售额统计:")
    print(f"  总销售额: {total_amount:,.2f} 元")
    print(f"  平均日销售额: {avg_daily_amount:,.2f} 元")
    print("=" * 60)


def main():
    """主函数"""
    # 设置随机种子保证可复现
    random.seed(42)

    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 加载商品数据
    products_file = os.path.join(script_dir, 'products.json')
    print("正在加载商品数据...")
    products = load_products(products_file)
    print(f"加载了 {len(products)} 个商品")

    # 计算时间范围：从当前日期往前推12个月（约365天）
    today = datetime.now()
    start_date = today - timedelta(days=365)

    print(f"\n时间范围: {start_date.strftime('%Y-%m-%d')} 到 {today.strftime('%Y-%m-%d')}")
    print("正在生成销量数据...")

    # 为每个商品生成日销量数据
    all_records = []

    for idx, product in enumerate(products, 1):
        product_id = product['product_id']
        price = product['price']

        # 生成该商品的日销量数据
        daily_records = generate_daily_sales_for_product(
            product_id=product_id,
            price=price,
            start_date=start_date,
            total_days=365
        )

        all_records.extend(daily_records)

        # 进度提示（每10个商品打印一次）
        if idx % 10 == 0 or idx == len(products):
            print(f"  进度: {idx}/{len(products)} 商品")

    print(f"共生成 {len(all_records):,} 条销量记录")

    # 保存到JSON文件
    output_file = os.path.join(script_dir, 'monthly_sales.json')
    print(f"\n正在保存数据到 {output_file}...")
    save_to_json(all_records, output_file)
    print(f"数据保存完成!")

    # 发送到Kafka（失败不影响JSON保存）
    print("\n尝试发送数据到Kafka...")
    try:
        send_to_kafka(all_records, topic='raw_monthly_sales')
    except Exception as e:
        print(f"Kafka发送失败: {e}")
        print("数据已保存到 monthly_sales.json，可稍后重试发送")

    # 打印统计信息
    print_statistics(all_records)


if __name__ == "__main__":
    main()
