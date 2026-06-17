"""
完整数据管道脚本
一键执行: 数据初始化 → HDFS上传 → Spark清洗 → Spark分析 → 指标计算

所有脚本通过 docker exec 在 backend 容器内执行，
确保网络环境与后端服务一致（能解析 hbase-master、elasticsearch 等容器域名）。

使用方式:
    cd 项目根目录
    uv run python scripts/run_pipeline.py
"""
import subprocess
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(cmd, desc="", check=True):
    """执行shell命令并打印输出"""
    print(f"\n{'='*60}")
    print(f"  {desc}")
    print(f"  命令: {cmd}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True, cwd=PROJECT_ROOT, capture_output=False)
    if check and result.returncode != 0:
        print(f"\n[错误] 命令失败 (退出码: {result.returncode})")
        return False
    return True


def docker_exec(container, script, desc=""):
    """在 Docker 容器内执行 Python 脚本"""
    cmd = f"docker exec {container} uv run --directory backend python /app/scripts/{script}"
    return run(cmd, desc)


def main():
    print("=" * 60)
    print("  抖音电商竞品分析 - 完整数据管道")
    print("=" * 60)
    print("\n  所有脚本在 backend 容器内执行，确保网络环境一致")

    # ========================================
    # 阶段0: 检查Docker服务状态
    # ========================================
    print("\n[阶段0] 检查Docker服务...")
    result = subprocess.run("docker compose ps",
                          shell=True, cwd=PROJECT_ROOT, capture_output=True, text=True, encoding='utf-8')
    services = result.stdout or ""
    required = ['hdfs-namenode', 'hdfs-datanode', 'hbase-master', 'elasticsearch', 'spark-master', 'backend']
    # 简单检测：服务名出现在输出中且包含 Up 就认为在运行
    missing = [s for s in required if s not in services]

    if missing:
        print(f"  [警告] 以下服务未运行: {', '.join(missing)}")
        print("  请先运行: docker compose up -d --build")
        return
    print("  所有必需服务已运行")

    # ========================================
    # 阶段1: 初始化 HBase + Elasticsearch
    # ========================================
    print("\n[阶段1] 初始化 HBase + Elasticsearch...")
    docker_exec("backend", "init_data.py", "写入商品/评价/销量数据到 HBase 和 ES")

    # ========================================
    # 阶段2: 上传数据到HDFS
    # ========================================
    print("\n[阶段2] 上传数据到HDFS...")

    # mock-data 已通过 volume 挂载到 backend 容器的 /app/mock-data/
    # 同时也挂载到 hdfs-namenode 的 /data/mock-data/

    # 创建HDFS目录
    run("docker exec hdfs-namenode hdfs dfs -mkdir -p /douyin/raw/products",
        "创建HDFS目录: /douyin/raw/products")
    run("docker exec hdfs-namenode hdfs dfs -mkdir -p /douyin/raw/reviews",
        "创建HDFS目录: /douyin/raw/reviews")
    run("docker exec hdfs-namenode hdfs dfs -mkdir -p /douyin/raw/monthly_sales",
        "创建HDFS目录: /douyin/raw/monthly_sales")
    run("docker exec hdfs-namenode hdfs dfs -mkdir -p /douyin/cleaned",
        "创建HDFS目录: /douyin/cleaned")
    run("docker exec hdfs-namenode hdfs dfs -mkdir -p /douyin/processed",
        "创建HDFS目录: /douyin/processed")

    # 上传数据文件
    for filename in ['products.json', 'reviews.json', 'monthly_sales.json']:
        topic = filename.replace('.json', '')
        run(f"docker exec hdfs-namenode hdfs dfs -put -f /data/mock-data/{filename} /douyin/raw/{topic}/",
            f"上传 {filename} 到 HDFS")

    # 验证HDFS数据
    run("docker exec hdfs-namenode hdfs dfs -ls /douyin/raw/", "验证HDFS数据")

    # ========================================
    # 阶段3: Spark数据清洗
    # ========================================
    print("\n[阶段3] Spark数据清洗...")
    run("docker exec spark-master /opt/spark/bin/spark-submit "
        "--master spark://spark-master:7077 "
        "/opt/spark-jobs/data_cleaning.py",
        "提交数据清洗作业")

    # ========================================
    # 阶段4: Spark商品分析（计算hot_score）
    # ========================================
    print("\n[阶段4] Spark商品分析...")
    run("docker exec spark-master /opt/spark/bin/spark-submit "
        "--master spark://spark-master:7077 "
        "/opt/spark-jobs/product_analysis_job.py",
        "提交商品分析作业")

    # ========================================
    # 阶段5: Spark评价分析
    # ========================================
    print("\n[阶段5] Spark评价分析...")
    run("docker exec spark-master /opt/spark/bin/spark-submit "
        "--master spark://spark-master:7077 "
        "/opt/spark-jobs/nlp_analysis_job.py",
        "提交评价分析作业")

    # ========================================
    # 阶段6: Spark趋势聚合
    # ========================================
    print("\n[阶段6] Spark趋势聚合...")
    run("docker exec spark-master /opt/spark/bin/spark-submit "
        "--master spark://spark-master:7077 "
        "/opt/spark-jobs/trend_aggregation_job.py",
        "提交趋势聚合作业")

    # ========================================
    # 阶段7: 计算分析指标（在 backend 容器内执行）
    # ========================================
    print("\n[阶段7] 计算分析指标（写入 HBase）...")
    docker_exec("backend", "compute_analysis.py", "计算商品分析指标")
    docker_exec("backend", "compute_review_analysis.py", "计算评价分析指标")

    # ========================================
    # 完成
    # ========================================
    print("\n" + "=" * 60)
    print("  数据管道执行完成!")
    print("=" * 60)
    print("\n服务访问地址:")
    print("  前端: http://localhost")
    print("  后端API: http://localhost:8000/docs")
    print("  Spark UI: http://localhost:8080")
    print("  HDFS: http://localhost:9870")
    print("  HBase: http://localhost:16010")
    print("  ES: http://localhost:9200")


if __name__ == "__main__":
    main()
