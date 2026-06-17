"""
电商数据洞察平台 - 数据管道 DAG

自动化流程:
1. 生成mock数据（模拟爬取）
2. 初始化HBase和Elasticsearch
3. 上传数据到HDFS
4. Spark数据清洗
5. Spark分析作业（商品分析、NLP分析、趋势聚合）
6. 计算分析指标
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

# 默认参数
default_args = {
    'owner': 'admin',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=2),
}

# DAG定义
with DAG(
    'ecommerce_etl_pipeline',
    default_args=default_args,
    description='电商数据洞察平台 - 数据管道每日自动执行',
    schedule_interval='0 2 * * *',  # 每天凌晨2点
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=['ecommerce', 'etl', 'spark'],
) as dag:

    # 开始标记
    start = EmptyOperator(task_id='start')

    # ==================== 阶段1: 数据生成 ====================
    generate_products = BashOperator(
        task_id='generate_products',
        bash_command='cd /opt/airflow/mock-data && python generate_products.py',
        doc='生成商品mock数据',
    )

    generate_reviews = BashOperator(
        task_id='generate_reviews',
        bash_command='cd /opt/airflow/mock-data && python generate_reviews.py',
        doc='生成评价mock数据',
    )

    generate_sales = BashOperator(
        task_id='generate_sales',
        bash_command='cd /opt/airflow/mock-data && python generate_monthly_sales.py',
        doc='生成销量mock数据',
    )

    # ==================== 阶段2: 初始化存储 ====================
    init_hbase_es = BashOperator(
        task_id='init_hbase_es',
        bash_command='cd /opt/airflow/scripts && python init_data.py',
        doc='初始化HBase和Elasticsearch',
    )

    # ==================== 阶段3: 上传HDFS ====================
    create_hdfs_dirs = BashOperator(
        task_id='create_hdfs_dirs',
        bash_command='docker exec hdfs-namenode hdfs dfs -mkdir -p /douyin/raw/products /douyin/raw/reviews /douyin/raw/monthly_sales',
        doc='创建HDFS目录',
    )

    upload_products = BashOperator(
        task_id='upload_products',
        bash_command='docker exec hdfs-namenode hdfs dfs -put -f /data/mock-data/products.json /douyin/raw/products/',
        doc='上传商品数据到HDFS',
    )

    upload_reviews = BashOperator(
        task_id='upload_reviews',
        bash_command='docker exec hdfs-namenode hdfs dfs -put -f /data/mock-data/reviews.json /douyin/raw/reviews/',
        doc='上传评价数据到HDFS',
    )

    upload_sales = BashOperator(
        task_id='upload_sales',
        bash_command='docker exec hdfs-namenode hdfs dfs -put -f /data/mock-data/monthly_sales.json /douyin/raw/monthly_sales/',
        doc='上传销量数据到HDFS',
    )

    # ==================== 阶段4: Spark数据清洗 ====================
    spark_cleaning = BashOperator(
        task_id='spark_cleaning',
        bash_command='docker exec spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --deploy-mode client /opt/spark-jobs/data_cleaning.py',
        doc='Spark数据清洗',
        execution_timeout=timedelta(hours=1),
    )

    # ==================== 阶段5: Spark分析作业 ====================
    spark_product_analysis = BashOperator(
        task_id='spark_product_analysis',
        bash_command='docker exec spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --deploy-mode client /opt/spark-jobs/product_analysis_job.py',
        doc='Spark商品分析',
        execution_timeout=timedelta(hours=1),
    )

    spark_nlp_analysis = BashOperator(
        task_id='spark_nlp_analysis',
        bash_command='docker exec spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --deploy-mode client /opt/spark-jobs/nlp_analysis_job.py',
        doc='Spark评价NLP分析',
        execution_timeout=timedelta(hours=1),
    )

    spark_trend_aggregation = BashOperator(
        task_id='spark_trend_aggregation',
        bash_command='docker exec spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --deploy-mode client /opt/spark-jobs/trend_aggregation_job.py',
        doc='Spark趋势聚合',
        execution_timeout=timedelta(hours=1),
    )

    # ==================== 阶段6: 计算分析指标 ====================
    compute_analysis = BashOperator(
        task_id='compute_analysis',
        bash_command='cd /opt/airflow/scripts && python compute_analysis.py',
        doc='计算商品分析指标',
        execution_timeout=timedelta(hours=1),
    )

    compute_review_analysis = BashOperator(
        task_id='compute_review_analysis',
        bash_command='cd /opt/airflow/scripts && python compute_review_analysis.py',
        doc='计算评价分析指标',
        execution_timeout=timedelta(hours=1),
    )

    # 结束标记
    finish = EmptyOperator(task_id='finish')

    # ==================== 任务依赖关系 ====================
    # 阶段1: 并行生成数据
    start >> [generate_products, generate_reviews, generate_sales]

    # 阶段2: 初始化存储（依赖所有数据生成完成）
    [generate_products, generate_reviews, generate_sales] >> init_hbase_es

    # 阶段3: 上传HDFS
    init_hbase_es >> create_hdfs_dirs
    create_hdfs_dirs >> [upload_products, upload_reviews, upload_sales]

    # 阶段4: Spark清洗（依赖所有上传完成）
    [upload_products, upload_reviews, upload_sales] >> spark_cleaning

    # 阶段5: Spark分析（并行执行，依赖清洗完成）
    spark_cleaning >> [spark_product_analysis, spark_nlp_analysis, spark_trend_aggregation]

    # 阶段6: 计算指标（依赖所有Spark分析完成）
    [spark_product_analysis, spark_nlp_analysis, spark_trend_aggregation] >> compute_analysis
    [spark_product_analysis, spark_nlp_analysis, spark_trend_aggregation] >> compute_review_analysis

    # 结束
    [compute_analysis, compute_review_analysis] >> finish
