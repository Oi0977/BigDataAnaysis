"""
Spark 商品分析计算作业
综合销量、评价、增长率计算商品爆款指数（hot_score）

输入:
  - HDFS /douyin/cleaned/products     — 清洗后商品数据
  - HDFS /douyin/cleaned/reviews      — 清洗后评价数据
  - HDFS /douyin/cleaned/monthly_sales — 清洗后日销量数据

输出:
  - HDFS /douyin/processed/product_analysis — 商品分析结果
  - HBase product_analysis 表 — 写入计算结果

计算逻辑:
  1. 从 monthly_sales 聚合销量指标
  2. 从 reviews 聚合评价指标
  3. 按品类归一化计算爆款指数 hot_score
  4. jieba 提取高频关键词作为 top_tags
"""

import json
import os
import sys
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, avg, sum as spark_sum, max as spark_max, when, lit,
    trim, collect_list, udf, desc
)
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType,
    ArrayType, IntegerType, LongType
)

# ============================================================
# 路径配置
# ============================================================
HDFS_CLEANED_BASE = "hdfs:///douyin/cleaned"
HDFS_PROCESSED_BASE = "hdfs:///douyin/processed"

LOCAL_MOCK_DIR = os.environ.get("LOCAL_MOCK_DIR", "/data/mock-data")


def read_local_json(spark, filepath, label=""):
    """用Python json读取文件再转Spark DataFrame，避免PySpark JSON解析兼容问题"""
    import json as pyjson
    with open(filepath, 'r', encoding='utf-8') as f:
        data = pyjson.load(f)
    if not isinstance(data, list):
        data = [data]
    df = spark.createDataFrame(data)
    print(f"  [本地] {label}: {df.count()} 条记录")
    return df


# ============================================================
# Jieba 关键词提取
# ============================================================
def extract_top_keywords(texts: list, top_n: int = 10) -> list:
    """
    从评价文本列表中提取高频关键词

    参数:
        texts: 评价文本列表
        top_n: 返回前N个关键词

    返回:
        关键词列表，如 ["质量", "物流", "性价比"]
    """
    try:
        import jieba
        from collections import Counter

        # 电商领域停用词
        stop_words = {
            '的', '了', '是', '在', '我', '有', '和', '就', '不', '人',
            '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
            '你', '会', '着', '没有', '看', '好', '自己', '这', '他', '她',
            '们', '那', '被', '从', '把', '还', '没', '过', '来', '对',
            '为', '以', '与', '或', '但', '而', '又', '能', '可', '吗',
            '啊', '吧', '呢', '哦', '哈', '嗯', '呀', '哇', '嘛', '啦',
            '么', '这个', '那个', '什么', '怎么', '这样', '那样', '可以',
            '比较', '真的', '确实', '非常', '特别', '其实', '觉得', '感觉',
            '因为', '所以', '如果', '虽然', '但是', '还是', '只是', '已经',
            '一下', '一些', '一点', '之后', '之前', '时候', '现在', '然后',
        }

        # 合并所有文本
        all_text = " ".join(texts)
        words = jieba.lcut(all_text)

        # 过滤：长度>1、非停用词、纯中文
        filtered = [
            w for w in words
            if len(w) > 1
            and w not in stop_words
            and all('一' <= c <= '鿿' for c in w)
        ]

        # 统计词频并返回Top N
        counter = Counter(filtered)
        return [word for word, _ in counter.most_common(top_n)]

    except ImportError:
        print("  [警告] jieba未安装，跳过关键词提取")
        return []
    except Exception as e:
        print(f"  [警告] 关键词提取失败: {e}")
        return []


# 注册为UDF（用于Spark DataFrame操作）
def udf_extract_keywords(text):
    """单条文本关键词提取（UDF版本）"""
    try:
        import jieba
        stop_words = {
            '的', '了', '是', '在', '我', '有', '和', '就', '不', '人',
            '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
            '你', '会', '着', '没有', '看', '好', '自己', '这', '他', '她',
            '们', '那', '被', '从', '把', '还', '没', '过', '来', '对',
            '为', '以', '与', '或', '但', '而', '又', '能', '可', '吗',
            '啊', '吧', '呢', '哦', '哈', '嗯', '呀', '哇', '嘛', '啦',
        }
        words = jieba.lcut(text)
        return [
            w for w in words
            if len(w) > 1
            and w not in stop_words
            and all('一' <= c <= '鿿' for c in w)
        ][:10]
    except Exception:
        return []


keywords_udf = udf(udf_extract_keywords, ArrayType(StringType()))


# ============================================================
# HBase 写入
# ============================================================
def write_to_hbase(results: list, table_name: str = "product_analysis"):
    """
    将商品分析结果写入HBase

    参数:
        results: 结果字典列表
        table_name: HBase表名

    HBase表结构:
        product_analysis:
          rowkey = product_id
          cf=metrics: hotScore, positiveRate, negativeRate, reviewCount,
                      avgRating, monthlyGrowth, topTags, updateTime
          cf=trend: salesTrend
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
                batch.put(rowkey, {
                    'metrics:hotScore': str(row.get('hot_score', 0)),
                    'metrics:positiveRate': str(row.get('positive_rate', 0)),
                    'metrics:negativeRate': str(row.get('negative_rate', 0)),
                    'metrics:reviewCount': str(row.get('review_count', 0)),
                    'metrics:avgRating': str(row.get('avg_rating', 0)),
                    'metrics:monthlyGrowth': str(row.get('monthly_growth', 0)),
                    'metrics:topTags': json.dumps(row.get('top_tags', []), ensure_ascii=False),
                    'metrics:updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'trend:salesTrend': json.dumps(row.get('sales_trend', []), ensure_ascii=False),
                })

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
def compute_sales_metrics(spark: SparkSession, sales_df):
    """
    从日销量数据聚合得到销量指标

    返回DataFrame包含:
      product_id, total_sales, latest_month_sales, last_month_sales, monthly_growth
    """
    print("\n--- 计算销量指标 ---")

    # 确保date为字符串类型，提取月份 (YYYY-MM)
    sales_with_month = sales_df \
        .withColumn("month", col("date").substr(1, 7)) \
        .withColumn("daily_sales_d", col("daily_sales").cast(DoubleType()))

    # 1. 总销量（近12月）
    total_sales = sales_with_month.groupBy("product_id").agg(
        spark_sum("daily_sales_d").alias("total_sales")
    )

    # 2. 按月聚合
    monthly_agg = sales_with_month.groupBy("product_id", "month").agg(
        spark_sum("daily_sales_d").alias("monthly_sales")
    )

    # 3. 获取最近两个月的月份名（按降序排列取前2）
    from pyspark.sql.window import Window
    from pyspark.sql.functions import row_number

    # 获取数据中最新的月份
    max_month = sales_with_month.agg(spark_max("month")).collect()[0][0]
    print(f"  数据最新月份: {max_month}")

    # 计算上个月
    if max_month:
        year, month = int(max_month[:4]), int(max_month[5:7])
        if month == 1:
            last_month = f"{year - 1}-12"
        else:
            last_month = f"{year}-{month - 1:02d}"
    else:
        last_month = None

    print(f"  最近月份: {max_month}, 上个月: {last_month}")

    # 4. 提取最近一个月和上个月的销量
    if max_month:
        latest_sales = monthly_agg.filter(col("month") == max_month) \
            .select("product_id", col("monthly_sales").alias("latest_month_sales"))
    else:
        latest_sales = spark.createDataFrame(
            [], StructType([
                StructField("product_id", StringType()),
                StructField("latest_month_sales", DoubleType())
            ])
        )

    if last_month:
        prev_sales = monthly_agg.filter(col("month") == last_month) \
            .select("product_id", col("monthly_sales").alias("last_month_sales"))
    else:
        prev_sales = spark.createDataFrame(
            [], StructType([
                StructField("product_id", StringType()),
                StructField("last_month_sales", DoubleType())
            ])
        )

    # 5. 合并所有销量指标
    result = total_sales \
        .join(latest_sales, "product_id", "left") \
        .join(prev_sales, "product_id", "left") \
        .withColumn("latest_month_sales",
                    when(col("latest_month_sales").isNull(), lit(0))
                    .otherwise(col("latest_month_sales"))) \
        .withColumn("last_month_sales",
                    when(col("last_month_sales").isNull(), lit(0))
                    .otherwise(col("last_month_sales"))) \
        .withColumn("monthly_growth",
                    when(col("last_month_sales") > 0,
                         ((col("latest_month_sales") - col("last_month_sales"))
                          / col("last_month_sales") * 100))
                    .otherwise(lit(0.0)))

    print(f"  销量指标计算完成，共 {result.count()} 个商品")
    return result


def compute_review_metrics(spark: SparkSession, reviews_df):
    """
    从评价数据聚合得到评价指标

    返回DataFrame包含:
      product_id, review_count, avg_rating, positive_count,
      negative_count, positive_rate, negative_rate, review_contents
    """
    print("\n--- 计算评价指标 ---")

    # 基础聚合
    review_stats = reviews_df.groupBy("product_id").agg(
        count("*").alias("review_count"),
        avg(col("rating").cast(DoubleType())).alias("avg_rating"),
        # 好评数 (rating >= 4)
        spark_sum(when(col("rating").cast(DoubleType()) >= 4, 1).otherwise(0)).alias("positive_count"),
        # 差评数 (rating <= 2)
        spark_sum(when(col("rating").cast(DoubleType()) <= 2, 1).otherwise(0)).alias("negative_count"),
        # 收集所有评价内容用于关键词提取
        collect_list("content").alias("review_contents")
    )

    # 计算好评率和差评率
    result = review_stats \
        .withColumn("positive_rate",
                    when(col("review_count") > 0,
                         col("positive_count").cast(DoubleType()) / col("review_count"))
                    .otherwise(lit(0.0))) \
        .withColumn("negative_rate",
                    when(col("review_count") > 0,
                         col("negative_count").cast(DoubleType()) / col("review_count"))
                    .otherwise(lit(0.0))) \
        .withColumn("avg_rating",
                    when(col("avg_rating").isNull(), lit(3.5))
                    .otherwise(col("avg_rating")))

    print(f"  评价指标计算完成，共 {result.count()} 个商品")
    return result


def compute_hot_score(spark: SparkSession, products_df, sales_metrics, review_metrics):
    """
    计算爆款指数 hot_score

    公式:
      sales_score = total_sales / 品类最大total_sales (归一化0-1)
      growth_score = min(monthly_growth / 100, 1.0)
      rating_score = avg_rating / 5.0
      review_score = min(review_count / 500, 1.0)
      hot_score = (0.4*sales_score + 0.3*growth_score + 0.2*rating_score + 0.1*review_score) * 1000

    参数:
        spark: SparkSession
        products_df: 商品基础数据
        sales_metrics: 销量指标DataFrame
        review_metrics: 评价指标DataFrame

    返回:
        完整的商品分析结果DataFrame
    """
    print("\n--- 计算爆款指数 ---")

    # 1. 合并商品基础数据、销量指标、评价指标
    combined = products_df \
        .join(sales_metrics, "product_id", "left") \
        .join(review_metrics.drop("review_contents"), "product_id", "left")

    # 2. 填充空值
    combined = combined \
        .withColumn("total_sales",
                    when(col("total_sales").isNull(), lit(0.0))
                    .otherwise(col("total_sales").cast(DoubleType()))) \
        .withColumn("review_count",
                    when(col("review_count").isNull(), lit(0))
                    .otherwise(col("review_count").cast(LongType()))) \
        .withColumn("avg_rating",
                    when(col("avg_rating").isNull(), lit(3.5))
                    .otherwise(col("avg_rating"))) \
        .withColumn("positive_rate",
                    when(col("positive_rate").isNull(), lit(0.0))
                    .otherwise(col("positive_rate"))) \
        .withColumn("negative_rate",
                    when(col("negative_rate").isNull(), lit(0.0))
                    .otherwise(col("negative_rate"))) \
        .withColumn("monthly_growth",
                    when(col("monthly_growth").isNull(), lit(0.0))
                    .otherwise(col("monthly_growth")))

    # 3. 计算品类最大total_sales（用于归一化）
    from pyspark.sql.window import Window
    category_max_window = Window.partitionBy("category")
    combined = combined.withColumn(
        "category_max_sales",
        spark_max("total_sales").over(category_max_window)
    )

    # 4. 计算各维度得分
    combined = combined \
        .withColumn("sales_score",
                    when(col("category_max_sales") > 0,
                         col("total_sales") / col("category_max_sales"))
                    .otherwise(lit(0.0))) \
        .withColumn("growth_score",
                    when(col("monthly_growth") / 100 > 1.0, lit(1.0))
                    .when(col("monthly_growth") / 100 < 0.0, lit(0.0))
                    .otherwise(col("monthly_growth") / 100)) \
        .withColumn("rating_score", col("avg_rating") / 5.0) \
        .withColumn("review_score",
                    when(col("review_count") / 500 > 1.0, lit(1.0))
                    .otherwise(col("review_count") / 500.0))

    # 5. 计算综合爆款指数
    combined = combined.withColumn(
        "hot_score",
        (col("sales_score") * 0.4 +
         col("growth_score") * 0.3 +
         col("rating_score") * 0.2 +
         col("review_score") * 0.1) * 1000
    )

    print(f"  爆款指数计算完成，共 {combined.count()} 个商品")
    return combined


def compute_top_tags(spark: SparkSession, review_metrics):
    """
    从评价内容中提取每个商品的高频关键词

    参数:
        review_metrics: 包含 review_contents 字段的DataFrame

    返回:
        DataFrame: product_id, top_tags
    """
    print("\n--- 提取高频关键词 ---")

    # 收集每个商品的所有评价内容
    product_contents = review_metrics.select(
        "product_id", "review_contents"
    ).collect()

    # 使用jieba提取关键词
    tag_results = []
    for row in product_contents:
        product_id = row["product_id"]
        contents = row["review_contents"] or []
        top_tags = extract_top_keywords(contents, top_n=10)
        tag_results.append({
            "product_id": product_id,
            "top_tags": top_tags
        })

    # 转为DataFrame
    schema = StructType([
        StructField("product_id", StringType()),
        StructField("top_tags", ArrayType(StringType()))
    ])
    tags_df = spark.createDataFrame(tag_results, schema)

    print(f"  关键词提取完成，共 {tags_df.count()} 个商品")
    return tags_df


def main():
    """主入口"""
    # 创建Spark会话（支持环境变量切换master）
    master_url = os.environ.get("SPARK_MASTER", "local[2]")
    spark = SparkSession.builder \
        .appName("EcommerceProductAnalysis") \
        .master(master_url) \
        .config("spark.sql.warehouse.dir", "hdfs:///user/hive/warehouse") \
        .getOrCreate()

    print("=" * 60)
    print("  电商数据洞察平台 - 商品分析作业")
    print("=" * 60)

    try:
        # ============================================================
        # 1. 读取清洗后的数据
        # ============================================================
        print("\n--- 读取数据 ---")

        # 读取商品数据
        try:
            products_df = spark.read.json(f"{HDFS_CLEANED_BASE}/products")
            print(f"  [HDFS] 商品数据: {products_df.count()} 条")
        except Exception:
            print(f"  [HDFS] 读取失败，尝试本地文件...")
            products_df = read_local_json(spark, os.path.join(LOCAL_MOCK_DIR, "products.json"), "商品数据")

        # 读取评价数据
        try:
            reviews_df = spark.read.json(f"{HDFS_CLEANED_BASE}/reviews")
            print(f"  [HDFS] 评价数据: {reviews_df.count()} 条")
        except Exception:
            print(f"  [HDFS] 读取失败，尝试本地文件...")
            reviews_df = read_local_json(spark, os.path.join(LOCAL_MOCK_DIR, "reviews.json"), "评价数据")

        # 读取日销量数据
        try:
            sales_df = spark.read.json(f"{HDFS_CLEANED_BASE}/monthly_sales")
            print(f"  [HDFS] 日销量数据: {sales_df.count()} 条")
        except Exception:
            print(f"  [HDFS] 读取失败，尝试本地文件...")
            sales_df = read_local_json(spark, os.path.join(LOCAL_MOCK_DIR, "monthly_sales.json"), "日销量数据")

        # ============================================================
        # 2. 计算销量指标
        # ============================================================
        sales_metrics = compute_sales_metrics(spark, sales_df)

        # ============================================================
        # 3. 计算评价指标
        # ============================================================
        review_metrics = compute_review_metrics(spark, reviews_df)

        # ============================================================
        # 4. 计算爆款指数
        # ============================================================
        analysis_result = compute_hot_score(spark, products_df, sales_metrics, review_metrics)

        # ============================================================
        # 5. 提取高频关键词
        # ============================================================
        top_tags_df = compute_top_tags(spark, review_metrics)

        # ============================================================
        # 6. 合并关键词到分析结果
        # ============================================================
        final_result = analysis_result.join(top_tags_df, "product_id", "left") \
            .withColumn("top_tags",
                        when(col("top_tags").isNull(), lit([]))
                        .otherwise(col("top_tags")))

        # ============================================================
        # 7. 输出到HDFS（可选，失败不影响后续HBase写入）
        # ============================================================
        print("\n--- 输出结果 ---")
        output_path = f"{HDFS_PROCESSED_BASE}/product_analysis"
        try:
            final_result.write.mode("overwrite").json(output_path)
            print(f"  商品分析结果已写入HDFS: {output_path}")
        except Exception as e:
            print(f"  [跳过] HDFS写入失败: {e}")

        # ============================================================
        # 8. 写入HBase
        # ============================================================
        # 收集结果用于HBase写入
        results_for_hbase = final_result.select(
            "product_id", "hot_score", "positive_rate", "negative_rate",
            "review_count", "avg_rating", "monthly_growth", "top_tags",
            "total_sales", "latest_month_sales", "last_month_sales",
            "sales_score", "growth_score", "rating_score", "review_score"
        ).collect()

        hbase_results = []
        for row in results_for_hbase:
            hbase_results.append({
                "product_id": row["product_id"],
                "hot_score": round(float(row["hot_score"] or 0), 2),
                "positive_rate": round(float(row["positive_rate"] or 0), 4),
                "negative_rate": round(float(row["negative_rate"] or 0), 4),
                "review_count": int(row["review_count"] or 0),
                "avg_rating": round(float(row["avg_rating"] or 0), 2),
                "monthly_growth": round(float(row["monthly_growth"] or 0), 2),
                "top_tags": row["top_tags"] if isinstance(row["top_tags"], list) else [],
            })

        write_to_hbase(hbase_results, "product_analysis")

        # ============================================================
        # 9. 打印Top 10热门商品
        # ============================================================
        print("\n" + "=" * 60)
        print("  Top 10 热门商品")
        print("=" * 60)
        top10 = final_result.select(
            "product_id", "name", "category", "hot_score",
            "total_sales", "avg_rating", "review_count"
        ).orderBy(desc("hot_score"))

        top10.show(10, truncate=False)

        # ============================================================
        # 打印各品类最高分
        # ============================================================
        print("\n--- 各品类最高爆款指数 ---")
        category_top = final_result.groupBy("category").agg(
            avg("hot_score").alias("avg_hot_score"),
            avg("total_sales").alias("avg_total_sales"),
            avg("avg_rating").alias("avg_rating")
        ).orderBy(desc("avg_hot_score"))
        category_top.show(truncate=False)

        print("\n" + "=" * 60)
        print("  商品分析计算完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n[错误] 商品分析作业失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        spark.stop()
        print("\n[完成] Spark会话已关闭")


if __name__ == "__main__":
    main()
