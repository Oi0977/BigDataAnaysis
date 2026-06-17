"""
Spark 数据清洗作业
从HDFS读取3种原始JSON数据，清洗后输出到HDFS cleaned目录

HDFS路径规划:
  输入: /douyin/raw/products/       — 商品原始数据
        /douyin/raw/reviews/        — 评价原始数据
        /douyin/raw/monthly_sales/  — 日销量原始数据
  输出: /douyin/cleaned/products    — 清洗后商品数据
        /douyin/cleaned/reviews     — 清洗后评价数据
        /douyin/cleaned/monthly_sales — 清洗后日销量数据

本地回退路径: mock-data/ 目录下的JSON文件
"""

import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, trim, when, length
from pyspark.sql.types import DoubleType


# ============================================================
# 路径配置
# ============================================================
HDFS_RAW_BASE = "hdfs:///douyin/raw"
HDFS_CLEANED_BASE = "hdfs:///douyin/cleaned"

# 本地回退路径（项目根目录下的 mock-data）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_MOCK_DIR = os.path.join(PROJECT_ROOT, "mock-data")


def create_spark_session() -> SparkSession:
    """创建Spark会话"""
    master_url = os.environ.get("SPARK_MASTER", "local[2]")
    return SparkSession.builder \
        .appName("DouyinDataCleaning") \
        .master(master_url) \
        .config("spark.sql.warehouse.dir", "hdfs:///user/hive/warehouse") \
        .config("spark.driver.extraJavaOptions", "-Djava.security.manager=allow") \
        .getOrCreate()


def read_data(spark: SparkSession, hdfs_path: str, local_path: str, label: str):
    """
    读取数据：优先从HDFS读取，如果HDFS不可用则从本地JSON文件读取

    参数:
        spark: SparkSession实例
        hdfs_path: HDFS路径
        local_path: 本地JSON文件路径
        label: 数据标签（用于日志输出）

    返回:
        DataFrame
    """
    try:
        # 尝试从HDFS读取
        print(f"  [HDFS] 尝试从 {hdfs_path} 读取 {label}...")
        df = spark.read.json(hdfs_path)
        count = df.count()
        print(f"  [HDFS] 成功读取 {label}: {count} 条记录")
        return df
    except Exception as hdfs_err:
        print(f"  [HDFS] 读取失败，尝试本地文件...")
        print(f"  [本地] 读取: {local_path}")
        try:
            # 用Python json加载，转Spark DataFrame（兼容性更好）
            import json as pyjson
            with open(local_path, 'r', encoding='utf-8') as f:
                data = pyjson.load(f)
            if not isinstance(data, list):
                data = [data]
            df = spark.createDataFrame(data)
            print(f"  [本地] 成功读取 {label}: {df.count()} 条记录")
            return df
        except Exception as local_err:
            print(f"  [本地] 读取也失败: {local_err}")
            raise RuntimeError(
                f"无法读取 {label} 数据。\n"
                f"  HDFS错误: {hdfs_err}\n"
                f"  本地错误: {local_err}"
            )


def clean_products(spark: SparkSession, raw_df):
    """
    清洗商品数据

    清洗规则:
    1. name: 去除首尾空格
    2. category: 去除首尾空格
    3. brand: 去除首尾空格
    4. description: 去除首尾空格
    5. shop_name: 去除首尾空格
    6. price < 0 设为 0
    7. original_price < 0 设为 0
    8. 过滤空名称记录
    9. 过滤空product_id记录
    """
    print("\n--- 清洗商品数据 ---")
    before_count = raw_df.count()

    cleaned = raw_df \
        .withColumn("name", trim(col("name"))) \
        .withColumn("category", trim(col("category"))) \
        .withColumn("brand", trim(col("brand"))) \
        .withColumn("description", trim(col("description"))) \
        .withColumn("shop_name", trim(col("shop_name"))) \
        .withColumn("price",
                    when(col("price").cast(DoubleType()).isNull() |
                         (col("price").cast(DoubleType()) < 0), 0)
                    .otherwise(col("price").cast(DoubleType()))) \
        .withColumn("original_price",
                    when(col("original_price").cast(DoubleType()).isNull() |
                         (col("original_price").cast(DoubleType()) < 0), 0)
                    .otherwise(col("original_price").cast(DoubleType()))) \
        .filter(col("product_id").isNotNull() & (col("product_id") != "")) \
        .filter(col("name").isNotNull() & (length(col("name")) > 0))

    after_count = cleaned.count()
    print(f"  清洗前: {before_count} 条 -> 清洗后: {after_count} 条")
    print(f"  过滤掉: {before_count - after_count} 条无效记录")
    return cleaned


def clean_reviews(spark: SparkSession, raw_df):
    """
    清洗评价数据

    清洗规则:
    1. content: 去除首尾空格
    2. username: 去除首尾空格
    3. rating 范围限制 1-5
    4. 过滤空内容记录
    5. 过滤空review_id记录
    """
    print("\n--- 清洗评价数据 ---")
    before_count = raw_df.count()

    cleaned = raw_df \
        .withColumn("content", trim(col("content"))) \
        .withColumn("username", trim(col("username"))) \
        .withColumn("rating",
                    when(col("rating").cast(DoubleType()) < 1, 1)
                    .when(col("rating").cast(DoubleType()) > 5, 5)
                    .otherwise(col("rating").cast(DoubleType()))) \
        .filter(col("review_id").isNotNull() & (col("review_id") != "")) \
        .filter(col("product_id").isNotNull() & (col("product_id") != "")) \
        .filter(col("content").isNotNull() & (length(col("content")) > 0))

    after_count = cleaned.count()
    print(f"  清洗前: {before_count} 条 -> 清洗后: {after_count} 条")
    print(f"  过滤掉: {before_count - after_count} 条无效记录")
    return cleaned


def clean_monthly_sales(spark: SparkSession, raw_df):
    """
    清洗日销量数据

    清洗规则:
    1. daily_sales < 0 设为 0
    2. daily_amount < 0 设为 0
    3. 过滤无效日期（date为空或格式错误）
    4. 过滤空product_id记录
    """
    print("\n--- 清洗日销量数据 ---")
    before_count = raw_df.count()

    cleaned = raw_df \
        .withColumn("daily_sales",
                    when(col("daily_sales").cast(DoubleType()).isNull() |
                         (col("daily_sales").cast(DoubleType()) < 0), 0)
                    .otherwise(col("daily_sales").cast(DoubleType()))) \
        .withColumn("daily_amount",
                    when(col("daily_amount").cast(DoubleType()).isNull() |
                         (col("daily_amount").cast(DoubleType()) < 0), 0)
                    .otherwise(col("daily_amount").cast(DoubleType()))) \
        .filter(col("product_id").isNotNull() & (col("product_id") != "")) \
        .filter(col("date").isNotNull() & (length(col("date").cast("string")) >= 10))

    after_count = cleaned.count()
    print(f"  清洗前: {before_count} 条 -> 清洗后: {after_count} 条")
    print(f"  过滤掉: {before_count - after_count} 条无效记录")
    return cleaned


def write_output(df, hdfs_path: str, label: str):
    """将DataFrame写入HDFS（失败不影响后续）"""
    print(f"\n  [写入] 正在将 {label} 写入 {hdfs_path}...")
    try:
        df.write.mode("overwrite").json(hdfs_path)
        print(f"  [写入] {label} 写入完成，共 {df.count()} 条记录")
    except Exception as e:
        print(f"  [跳过] HDFS写入失败: {e}")


def main():
    """主入口"""
    # 创建Spark会话
    spark = create_spark_session()

    print("=" * 60)
    print("  抖音电商数据清洗作业")
    print("=" * 60)

    try:
        # ============================================================
        # 1. 清洗商品数据
        # ============================================================
        raw_products = read_data(
            spark,
            hdfs_path=f"{HDFS_RAW_BASE}/products/",
            local_path=os.path.join(LOCAL_MOCK_DIR, "products.json"),
            label="商品数据"
        )
        cleaned_products = clean_products(spark, raw_products)
        write_output(cleaned_products, f"{HDFS_CLEANED_BASE}/products", "商品数据")

        # ============================================================
        # 2. 清洗评价数据
        # ============================================================
        raw_reviews = read_data(
            spark,
            hdfs_path=f"{HDFS_RAW_BASE}/reviews/",
            local_path=os.path.join(LOCAL_MOCK_DIR, "reviews.json"),
            label="评价数据"
        )
        cleaned_reviews = clean_reviews(spark, raw_reviews)
        write_output(cleaned_reviews, f"{HDFS_CLEANED_BASE}/reviews", "评价数据")

        # ============================================================
        # 3. 清洗日销量数据
        # ============================================================
        raw_sales = read_data(
            spark,
            hdfs_path=f"{HDFS_RAW_BASE}/monthly_sales/",
            local_path=os.path.join(LOCAL_MOCK_DIR, "monthly_sales.json"),
            label="日销量数据"
        )
        cleaned_sales = clean_monthly_sales(spark, raw_sales)
        write_output(cleaned_sales, f"{HDFS_CLEANED_BASE}/monthly_sales", "日销量数据")

        # ============================================================
        # 打印清洗汇总
        # ============================================================
        print("\n" + "=" * 60)
        print("  数据清洗完成！")
        print("=" * 60)
        print(f"  商品数据:    {cleaned_products.count()} 条 -> {HDFS_CLEANED_BASE}/products")
        print(f"  评价数据:    {cleaned_reviews.count()} 条 -> {HDFS_CLEANED_BASE}/reviews")
        print(f"  日销量数据:  {cleaned_sales.count()} 条 -> {HDFS_CLEANED_BASE}/monthly_sales")
        print("=" * 60)

    except Exception as e:
        print(f"\n[错误] 数据清洗作业失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        spark.stop()
        print("\n[完成] Spark会话已关闭")


if __name__ == "__main__":
    main()
