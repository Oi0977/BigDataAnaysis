FROM apache/airflow:2.8.0

# 只安装项目需要的依赖（Airflow 镜像已包含 psycopg2 和 redis）
USER root
RUN apt-get update && apt-get install -y gcc docker.io && rm -rf /var/lib/apt/lists/*

USER airflow
RUN pip install --no-cache-dir \
    happybase \
    jieba \
    snownlp
