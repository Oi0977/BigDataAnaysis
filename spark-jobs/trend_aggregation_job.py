"""
Spark 趋势聚合作业
从日销量数据聚合得到月度趋势数据

输入:
  - HDFS /douyin/cleaned/monthly_sales — 清洗后日销量数据
  - HDFS /douyin/cleaned/products     — 清洗后商品数据（用于品类信息）

输出:
  - HDFS /douyin/processed/trend_data — 月度趋势数据
  - HBase trend_data 表 — 写入趋势数据

计算逻辑:
  1. 从 daily_sales 聚合为 monthly_sales（按 product_id + month 聚合）
  2. 生成近12个月的月度销量数组（sales_trend）
  3. 按品类聚合月度趋势（category_trend）
"""

import json
import os
import sys
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, sum as spark_sum, round as spark_round,
    collect_list, struct, when, lit, avg
)
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType,
    ArrayType, LongType, IntegerType, MapType
)


# ============================================================
# 路径配置
# ============================================================
HDFS_CLEANED_BASE = "hdfs:///douyin/cleaned"
HDFS_PROCESSED_BASE = "hdfs:///douyin/processed"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_MOCK_DIR = os.path.join(PROJECT_ROOT, "mock-data")


def read_local_json(spark, filepath, label=""):
    """用Python json读取文件再转Spark DataFrame"""
    import json as pyjson
    with open(filepath, 'r', encoding='utf-8') as f:
        data = pyjson.load(f)
    if not isinstance(data, list):
        data = [data]
    df = spark.createDataFrame(data)
    print(f"  [本地] {label}: {df.count()} 条记录")
    return df


# ============================================================
# HBase 写入
# ============================================================
def write_to_hbase(results: list, table_name: str = "trend_data"):
    """
    将趋势数据写入HBase

    HBase表结构:
        trend_data:
          rowkey = product_id
          cf=monthly: YYYY-MM:sales, YYYY-MM:amount, ...
    """
    try:
        import happybase

        print(f"\n[HBase] 正在连接HBase (localhost:9090)...")
        connection = happybase.Connection('localhost', port=9090)
        table = connection.table(table_name)

        print(f"[HBase] 正在写入 {table_name} 表...")

        with table.batch() as batch:
            for row in results:
                rowkey = row['product_id']

                # 构建月度数据列
                monthly_data = {}
                monthly_detail = row.get('monthly_detail', [])
                for item in monthly_detail:
                    month = item['month']
                    monthly_data[f'monthly:{month}:sales'] = str(item['monthly_sales'])
                    monthly_data[f'monthly:{month}:amount'] = str(item['monthly_amount'])

                # 写入汇总信息
                monthly_data['monthly:totalSales'] = str(row.get('total_sales', 0))
                monthly_data['monthly:totalAmount'] = str(row.get('total_amount', 0))
                monthly_data['monthly:avgMonthlySales'] = str(row.get('avg_monthly_sales', 0))
                monthly_data['monthly:updateTime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                batch.put(rowkey, monthly_data)

        connection.close()
        print(f"[HBase] 成功写入 {len(results)} 条记录到 {table_name} 表")

    except ImportError:
        print("[HBase] happybase未安装，跳过HBase写入")
    except Exception as e:
        print(f"[HBase] 写入失败: {e}")
        print("[HBase] 数据已保存到HDFS，HBase写入可稍后重试")


# ============================================================
# 主计算逻辑
# ============================================================
def aggregate_monthly_sales(spark: SparkSession, sales_df):
    """
    从日销量数据聚合为月度销量

    参数:
        sales_df: 日销量DataFrame

    返回:
        DataFrame: product_id, month, monthly_sales, monthly_amount
    """
    print("\n--- 聚合月度销量 ---")

    # 提取月份 (YYYY-MM)
    sales_with_month = sales_df \
        .withColumn("month", col("date").substr(1, 7)) \
        .withColumn("daily_sales_d", col("daily_sales").cast(DoubleType())) \
        .withColumn("daily_amount_d", col("daily_amount").cast(DoubleType()))

    # 按 product_id + month 聚合
    monthly_agg = sales_with_month.groupBy("product_id", "month").agg(
        spark_sum("daily_sales_d").alias("monthly_sales"),
        spark_sum("daily_amount_d").alias("monthly_amount")
    ).orderBy("product_id", "month")

    count = monthly_agg.count()
    print(f"  月度聚合完成，共 {count} 条记录")
    return monthly_agg


def generate_sales_trend(spark: SparkSession, monthly_agg_df):
    """
    为每个商品生成近12个月的月度销量数组

    参数:
        monthly_agg_df: 月度聚合DataFrame

    返回:
        每个商品的月度趋势数据列表
    """
    print("\n--- 生成月度趋势数组 ---")

    # 收集所有月份信息
    all_months = sorted([
        row["month"] for row in monthly_agg_df.select("month").distinct().collect()
    ])
    print(f"  数据覆盖月份: {all_months[0]} 到 {all_months[-1]}，共 {len(all_months)} 个月")

    # 取最近12个月（如果不足12个月则取全部）
    recent_12_months = all_months[-12:] if len(all_months) > 12 else all_months
    print(f"  使用最近 {len(recent_12_months)} 个月: {recent_12_months[0]} ~ {recent_12_months[-1]}")

    # 按商品聚合月度数据
    product_monthly = monthly_agg_df.groupBy("product_id").agg(
        collect_list(
            struct("month", "monthly_sales", "monthly_amount")
        ).alias("monthly_data")
    ).collect()

    results = []
    for row in product_monthly:
        product_id = row["product_id"]
        monthly_data = row["monthly_data"] or []

        # 构建月份 -> 数据的映射
        month_map = {}
        for item in monthly_data:
            month_map[item["month"]] = {
                "monthly_sales": float(item["monthly_sales"] or 0),
                "monthly_amount": float(item["monthly_amount"] or 0),
            }

        # 生成近12个月的销量和销售额数组
        sales_trend = []
        amount_trend = []
        monthly_detail = []

        for month in recent_12_months:
            data = month_map.get(month, {"monthly_sales": 0, "monthly_amount": 0})
            sales_trend.append(int(data["monthly_sales"]))
            amount_trend.append(round(data["monthly_amount"], 2))
            monthly_detail.append({
                "month": month,
                "monthly_sales": int(data["monthly_sales"]),
                "monthly_amount": round(data["monthly_amount"], 2),
            })

        # 计算汇总统计
        total_sales = sum(sales_trend)
        total_amount = sum(amount_trend)
        avg_monthly_sales = round(total_sales / len(recent_12_months), 1) if recent_12_months else 0

        results.append({
            "product_id": product_id,
            "sales_trend": sales_trend,
            "amount_trend": amount_trend,
            "monthly_detail": monthly_detail,
            "total_sales": total_sales,
            "total_amount": round(total_amount, 2),
            "avg_monthly_sales": avg_monthly_sales,
        })

    print(f"  趋势数组生成完成，共 {len(results)} 个商品")
    return results, recent_12_months


def compute_category_trend(spark: SparkSession, products_df, trend_results, recent_months):
    """
    按品类聚合月度趋势

    参数:
        products_df: 商品数据（包含 category 字段）
        trend_results: 商品趋势结果列表
        recent_months: 近12个月的月份列表

    返回:
        字典: { "手机": [月度销量数组], "电脑": [...], ... }
    """
    print("\n--- 按品类聚合趋势 ---")

    # 获取 product_id -> category 的映射
    product_category = {
        row["product_id"]: row["category"]
        for row in products_df.select("product_id", "category").collect()
    }

    # 按品类聚合
    category_monthly = {}
    for result in trend_results:
        product_id = result["product_id"]
        category = product_category.get(product_id, "未知")

        if category not in category_monthly:
            category_monthly[category] = [0] * len(recent_months)

        for i, sales in enumerate(result["sales_trend"]):
            category_monthly[category][i] += sales

    # 转为输出格式
    category_trend = {}
    for category, monthly_sales in category_monthly.items():
        category_trend[category] = {
            "months": recent_months,
            "monthly_sales": monthly_sales,
            "total_sales": sum(monthly_sales),
        }

    print(f"  品类趋势聚合完成，共 {len(category_trend)} 个品类:")
    for cat, data in category_trend.items():
        print(f"    {cat}: 总销量 {data['total_sales']}, "
              f"月均 {round(data['total_sales'] / len(recent_months))}")

    return category_trend


def main():
    """主入口"""
    # 创建Spark会话
    master_url = os.environ.get("SPARK_MASTER", "local[2]")
    spark = SparkSession.builder \
        .appName("DouyinTrendAggregation") \
        .master(master_url) \
        .config("spark.sql.warehouse.dir", "hdfs:///user/hive/warehouse") \
        .config("spark.driver.extraJavaOptions", "-Djava.security.manager=allow") \
        .getOrCreate()

    print("=" * 60)
    print("  抖音电商趋势聚合作业")
    print("=" * 60)

    try:
        # ============================================================
        # 1. 读取清洗后的数据
        # ============================================================
        print("\n--- 读取数据 ---")

        # 读取日销量数据
        try:
            sales_df = spark.read.json(f"{HDFS_CLEANED_BASE}/monthly_sales")
            print(f"  [HDFS] 日销量数据: {sales_df.count()} 条")
        except Exception:
            print(f"  [HDFS] 读取失败，尝试本地文件...")
            sales_df = read_local_json(spark, os.path.join(LOCAL_MOCK_DIR, "monthly_sales.json"), "日销量数据")
        # 读取商品数据（用于品类信息）
        try:
            products_df = spark.read.json(f"{HDFS_CLEANED_BASE}/products")
            print(f"  [HDFS] 商品数据: {products_df.count()} 条")
        except Exception:
            print(f"  [HDFS] 读取失败，尝试本地文件...")
            products_df = read_local_json(spark, os.path.join(LOCAL_MOCK_DIR, "products.json"), "商品数据")

        # ============================================================
        # 2. 聚合月度销量
        # ============================================================
        monthly_agg = aggregate_monthly_sales(spark, sales_df)

        # ============================================================
        # 3. 生成月度趋势数组
        # ============================================================
        trend_results, recent_months = generate_sales_trend(spark, monthly_agg)

        # ============================================================
        # 4. 按品类聚合趋势
        # ============================================================
        category_trend = compute_category_trend(
            spark, products_df, trend_results, recent_months
        )

        # ============================================================
        # 5. 输出到HDFS
        # ============================================================
        print("\n--- 输出结果 ---")

        # 5.1 输出商品维度的趋势数据
        product_trend_schema = StructType([
            StructField("product_id", StringType()),
            StructField("sales_trend", StringType()),  # JSON数组
            StructField("amount_trend", StringType()),  # JSON数组
            StructField("monthly_detail", StringType()),  # JSON数组
            StructField("total_sales", DoubleType()),
            StructField("total_amount", DoubleType()),
            StructField("avg_monthly_sales", DoubleType()),
        ])

        product_trend_rows = []
        for r in trend_results:
            product_trend_rows.append({
                "product_id": r["product_id"],
                "sales_trend": json.dumps(r["sales_trend"]),
                "amount_trend": json.dumps(r["amount_trend"]),
                "monthly_detail": json.dumps(r["monthly_detail"], ensure_ascii=False),
                "total_sales": r["total_sales"],
                "total_amount": r["total_amount"],
                "avg_monthly_sales": r["avg_monthly_sales"],
            })

        product_trend_df = spark.createDataFrame(product_trend_rows, product_trend_schema)
        output_path = f"{HDFS_PROCESSED_BASE}/trend_data"
        try:
            product_trend_df.write.mode("overwrite").json(output_path)
            print(f"  商品趋势数据已写入HDFS: {output_path}")
        except Exception as e:
            print(f"  [跳过] HDFS写入失败: {e}")

        # 5.2 输出品类维度的趋势数据
        category_trend_schema = StructType([
            StructField("category", StringType()),
            StructField("months", StringType()),  # JSON数组
            StructField("monthly_sales", StringType()),  # JSON数组
            StructField("total_sales", DoubleType()),
        ])

        category_trend_rows = []
        for cat, data in category_trend.items():
            category_trend_rows.append({
                "category": cat,
                "months": json.dumps(data["months"]),
                "monthly_sales": json.dumps(data["monthly_sales"]),
                "total_sales": data["total_sales"],
            })

        category_trend_df = spark.createDataFrame(category_trend_rows, category_trend_schema)
        category_output_path = f"{HDFS_PROCESSED_BASE}/category_trend"
        category_trend_df.write.mode("overwrite").json(category_output_path)
        print(f"  品类趋势数据已写入: {category_output_path}")

        # ============================================================
        # 6. 写入HBase
        # ============================================================
        write_to_hbase(trend_results, "trend_data")

        # ============================================================
        # 7. 打印趋势摘要
        # ============================================================
        print("\n" + "=" * 60)
        print("  趋势聚合完成！")
        print("=" * 60)
        print(f"  商品数:     {len(trend_results)} 个")
        print(f"  品类数:     {len(category_trend)} 个")
        print(f"  覆盖月份:   {recent_months[0]} ~ {recent_months[-1]}")

        # 显示Top 5商品趋势
        print("\n--- Top 5 销量商品趋势 ---")
        top5 = sorted(trend_results, key=lambda x: x["total_sales"], reverse=True)[:5]
        for r in top5:
            print(f"  {r['product_id']}: 总销量={r['total_sales']}, "
                  f"月均={r['avg_monthly_sales']}, "
                  f"趋势={r['sales_trend'][:6]}...")

        # 显示品类趋势
        print("\n--- 各品类月度销量趋势 ---")
        for cat, data in sorted(category_trend.items(),
                                key=lambda x: x[1]["total_sales"],
                                reverse=True):
            trend_str = str(data["monthly_sales"][:6]) + "..."
            print(f"  {cat}: 总销量={data['total_sales']}, 趋势={trend_str}")

        print("\n" + "=" * 60)
        print("  趋势聚合全部完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n[错误] 趋势聚合作业失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        spark.stop()
        print("\n[完成] Spark会话已关闭")


if __name__ == "__main__":
    main()
