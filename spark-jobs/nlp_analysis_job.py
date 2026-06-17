"""
Spark 评价NLP分析作业
使用 jieba 分词和 SnowNLP 情感分析处理评价数据

输入:
  - HDFS /douyin/cleaned/reviews — 清洗后评价数据

输出:
  - HDFS /douyin/processed/review_analysis — 按商品聚合的评价分析结果
  - HBase review_analysis 表 — 写入分析结果

分析内容:
  1. jieba 提取每条评价的关键词
  2. SnowNLP 情感分析（positive / neutral / negative）
  3. 按商品聚合：高频关键词、情感分布、评分分布
"""

import json
import os
import sys
from datetime import datetime
from collections import Counter

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, avg, udf, when, lit,
    collect_list, round as spark_round
)
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType,
    ArrayType, IntegerType, LongType, MapType
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

# 电商领域停用词
STOP_WORDS = {
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


# ============================================================
# NLP 函数
# ============================================================
def extract_keywords(text: str, top_n: int = 10) -> list:
    """
    使用 jieba 提取关键词

    参数:
        text: 输入文本
        top_n: 返回前N个关键词

    返回:
        关键词列表
    """
    try:
        import jieba
        words = jieba.lcut(text)
        filtered = [
            w for w in words
            if len(w) > 1
            and w not in STOP_WORDS
            and all('一' <= c <= '鿿' for c in w)
        ]
        return filtered[:top_n]
    except ImportError:
        return []
    except Exception:
        return []


def analyze_sentiment(text: str) -> str:
    """
    使用 SnowNLP 进行情感分析

    参数:
        text: 输入文本

    返回:
        "positive" / "neutral" / "negative"
    """
    try:
        from snownlp import SnowNLP
        score = SnowNLP(text).sentiments
        if score < 0.3:
            return "negative"
        elif score < 0.7:
            return "neutral"
        else:
            return "positive"
    except ImportError:
        return "neutral"
    except Exception:
        return "neutral"


# 注册UDF
keywords_udf = udf(extract_keywords, ArrayType(StringType()))
sentiment_udf = udf(analyze_sentiment, StringType())


# ============================================================
# HBase 写入
# ============================================================
def write_to_hbase(results: list, table_name: str = "review_analysis"):
    """
    将评价分析结果写入HBase

    HBase表结构:
        review_analysis:
          rowkey = product_id
          cf=stats: highFreqKeywords, sentimentDistribution,
                    ratingDistribution, updateTime
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
                    'stats:highFreqKeywords': json.dumps(
                        row.get('high_freq_keywords', []), ensure_ascii=False
                    ),
                    'stats:sentimentDistribution': json.dumps(
                        row.get('sentiment_distribution', {}), ensure_ascii=False
                    ),
                    'stats:ratingDistribution': json.dumps(
                        row.get('rating_distribution', {}), ensure_ascii=False
                    ),
                    'stats:updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
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
def analyze_reviews(spark: SparkSession, reviews_df):
    """
    对评价数据进行NLP分析

    步骤:
    1. jieba提取每条评价的关键词
    2. SnowNLP情感分析
    3. 返回添加了分析列的DataFrame
    """
    print("\n--- NLP分析 ---")

    # 注册UDF并执行分析
    analyzed = reviews_df \
        .withColumn("nlp_keywords", keywords_udf(col("content"))) \
        .withColumn("nlp_sentiment", sentiment_udf(col("content")))

    # 统计情感分布
    print("\n  情感分布统计:")
    sentiment_stats = analyzed.groupBy("nlp_sentiment").count()
    sentiment_stats.show(truncate=False)

    # 统计评分分布
    print("  评分分布统计:")
    rating_stats = analyzed.groupBy(
        col("rating").cast(IntegerType()).alias("rating")
    ).count().orderBy("rating")
    rating_stats.show(truncate=False)

    return analyzed


def aggregate_by_product(spark: SparkSession, analyzed_df):
    """
    按商品聚合评价分析结果

    聚合内容:
    - 高频关键词（合并所有评价的关键词，统计词频取Top10）
    - 情感分布（positive/neutral/negative各多少条）
    - 评分分布（1-5分各多少条）
    - 平均评分
    - 评价总数
    """
    print("\n--- 按商品聚合 ---")

    # 收集每个商品的所有评价数据
    product_data = analyzed_df.groupBy("product_id").agg(
        count("*").alias("review_count"),
        avg(col("rating").cast(DoubleType())).alias("avg_rating"),
        collect_list("nlp_keywords").alias("all_keywords"),
        collect_list("nlp_sentiment").alias("all_sentiments"),
        collect_list(col("rating").cast(IntegerType()).alias("rating_int")).alias("all_ratings")
    ).collect()

    results = []
    for row in product_data:
        product_id = row["product_id"]
        review_count = row["review_count"]
        avg_rating = float(row["avg_rating"] or 0)

        # ---- 高频关键词 ----
        all_keywords = []
        for kw_list in (row["all_keywords"] or []):
            if kw_list:
                all_keywords.extend(kw_list)

        # 统计词频取Top10
        keyword_counter = Counter(all_keywords)
        high_freq_keywords = [
            {"keyword": word, "count": cnt}
            for word, cnt in keyword_counter.most_common(10)
        ]

        # ---- 情感分布 ----
        sentiments = row["all_sentiments"] or []
        sentiment_counter = Counter(sentiments)
        sentiment_distribution = {
            "positive": sentiment_counter.get("positive", 0),
            "neutral": sentiment_counter.get("neutral", 0),
            "negative": sentiment_counter.get("negative", 0),
        }

        # ---- 评分分布 ----
        ratings = row["all_ratings"] or []
        rating_counter = Counter(ratings)
        rating_distribution = {
            str(r): rating_counter.get(r, 0)
            for r in range(1, 6)
        }

        results.append({
            "product_id": product_id,
            "review_count": review_count,
            "avg_rating": round(avg_rating, 2),
            "high_freq_keywords": high_freq_keywords,
            "sentiment_distribution": sentiment_distribution,
            "rating_distribution": rating_distribution,
        })

    print(f"  聚合完成，共 {len(results)} 个商品")
    return results


def main():
    """主入口"""
    # 创建Spark会话
    master_url = os.environ.get("SPARK_MASTER", "local[2]")
    spark = SparkSession.builder \
        .appName("DouyinNLPAnalysis") \
        .master(master_url) \
        .config("spark.sql.warehouse.dir", "hdfs:///user/hive/warehouse") \
        .config("spark.driver.extraJavaOptions", "-Djava.security.manager=allow") \
        .getOrCreate()

    print("=" * 60)
    print("  抖音电商评价NLP分析作业")
    print("=" * 60)

    try:
        # ============================================================
        # 1. 读取清洗后的评价数据
        # ============================================================
        print("\n--- 读取数据 ---")
        try:
            reviews_df = spark.read.json(f"{HDFS_CLEANED_BASE}/reviews")
            print(f"  [HDFS] 评价数据: {reviews_df.count()} 条")
        except Exception:
            print(f"  [HDFS] 读取失败，尝试本地文件...")
            reviews_df = read_local_json(spark, os.path.join(LOCAL_MOCK_DIR, "reviews.json"), "评价数据")
            print(f"  [本地] 评价数据: {reviews_df.count()} 条")

        # ============================================================
        # 2. NLP分析（关键词提取 + 情感分析）
        # ============================================================
        analyzed_df = analyze_reviews(spark, reviews_df)

        # ============================================================
        # 3. 按商品聚合
        # ============================================================
        aggregated_results = aggregate_by_product(spark, analyzed_df)

        # ============================================================
        # 4. 输出到HDFS
        # ============================================================
        print("\n--- 输出结果 ---")

        # 将聚合结果转为DataFrame
        schema = StructType([
            StructField("product_id", StringType()),
            StructField("review_count", LongType()),
            StructField("avg_rating", DoubleType()),
            StructField("high_freq_keywords", StringType()),  # JSON字符串
            StructField("sentiment_distribution", StringType()),  # JSON字符串
            StructField("rating_distribution", StringType()),  # JSON字符串
        ])

        output_rows = []
        for r in aggregated_results:
            output_rows.append({
                "product_id": r["product_id"],
                "review_count": r["review_count"],
                "avg_rating": r["avg_rating"],
                "high_freq_keywords": json.dumps(r["high_freq_keywords"], ensure_ascii=False),
                "sentiment_distribution": json.dumps(r["sentiment_distribution"], ensure_ascii=False),
                "rating_distribution": json.dumps(r["rating_distribution"], ensure_ascii=False),
            })

        output_df = spark.createDataFrame(output_rows, schema)
        output_path = f"{HDFS_PROCESSED_BASE}/review_analysis"
        try:
            output_df.write.mode("overwrite").json(output_path)
            print(f"  评价分析结果已写入HDFS: {output_path}")
        except Exception as e:
            print(f"  [跳过] HDFS写入失败: {e}")

        # ============================================================
        # 5. 写入HBase
        # ============================================================
        write_to_hbase(aggregated_results, "review_analysis")

        # ============================================================
        # 6. 打印分析摘要
        # ============================================================
        print("\n" + "=" * 60)
        print("  评价NLP分析完成！")
        print("=" * 60)
        print(f"  分析商品数: {len(aggregated_results)} 个")
        print(f"  总评价数:   {reviews_df.count()} 条")

        # 显示样例
        print("\n--- 分析样例 (前5个商品) ---")
        for r in aggregated_results[:5]:
            print(f"\n  商品: {r['product_id']}")
            print(f"    评价数: {r['review_count']}, 平均评分: {r['avg_rating']}")
            print(f"    情感分布: {r['sentiment_distribution']}")
            print(f"    高频关键词: {[kw['keyword'] for kw in r['high_freq_keywords'][:5]]}")

        print("\n" + "=" * 60)
        print("  评价NLP分析全部完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n[错误] NLP分析作业失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        spark.stop()
        print("\n[完成] Spark会话已关闭")


if __name__ == "__main__":
    main()
