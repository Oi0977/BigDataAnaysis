"""
完整数据管道脚本
一键执行: 数据上传HDFS → Spark清洗 → Spark分析 → HBase写入

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


def main():
    print("=" * 60)
    print("  抖音电商竞品分析 - 完整数据管道")
    print("=" * 60)

    # ========================================
    # 阶段1: 检查Docker服务状态
    # ========================================
    print("\n[阶段0] 检查Docker服务...")
    result = subprocess.run("docker-compose ps --format '{{.Name}} {{.Status}}'",
                          shell=True, cwd=PROJECT_ROOT, capture_output=True, text=True)
    services = result.stdout
    required = ['hdfs-namenode', 'hdfs-datanode', 'hbase-master', 'elasticsearch', 'spark-master']
    missing = [s for s in required if s not in services or 'Up' not in services.split(s)[1].split('\n')[0]]

    if missing:
        print(f"  [警告] 以下服务未运行: {', '.join(missing)}")
        print("  请先运行: docker-compose up -d")
        return
    print("  所有必需服务已运行")

    # ========================================
    # 阶段1: 上传数据到HDFS
    # ========================================
    print("\n[阶段1] 上传数据到HDFS...")

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

    # 上传数据文件（文件已通过volume挂载到 /data/mock-data/）
    for filename in ['products.json', 'reviews.json', 'monthly_sales.json']:
        topic = filename.replace('.json', '')
        run(f"docker exec hdfs-namenode hdfs dfs -put -f /data/mock-data/{filename} /douyin/raw/{topic}/",
            f"上传 {filename} 到 HDFS")

    # 验证HDFS数据
    run("docker exec hdfs-namenode hdfs dfs -ls /douyin/raw/", "验证HDFS数据")

    # ========================================
    # 阶段2: Spark数据清洗
    # ========================================
    print("\n[阶段2] Spark数据清洗...")
    run("docker exec spark-master /opt/spark/bin/spark-submit "
        "--master spark://spark-master:7077 "
        "--conf spark.driver.extraJavaOptions='-Djava.security.manager=allow' "
        "/opt/spark-jobs/data_cleaning.py",
        "提交数据清洗作业")

    # ========================================
    # 阶段3: Spark商品分析（计算hot_score）
    # ========================================
    print("\n[阶段3] Spark商品分析...")
    run("docker exec spark-master /opt/spark/bin/spark-submit "
        "--master spark://spark-master:7077 "
        "--conf spark.driver.extraJavaOptions='-Djava.security.manager=allow' "
        "/opt/spark-jobs/product_analysis_job.py",
        "提交商品分析作业")

    # ========================================
    # 阶段4: Spark评价分析
    # ========================================
    print("\n[阶段4] Spark评价分析...")
    run("docker exec spark-master /opt/spark/bin/spark-submit "
        "--master spark://spark-master:7077 "
        "--conf spark.driver.extraJavaOptions='-Djava.security.manager=allow' "
        "/opt/spark-jobs/nlp_analysis_job.py",
        "提交评价分析作业")

    # ========================================
    # 阶段5: Spark趋势聚合
    # ========================================
    print("\n[阶段5] Spark趋势聚合...")
    run("docker exec spark-master /opt/spark/bin/spark-submit "
        "--master spark://spark-master:7077 "
        "--conf spark.driver.extraJavaOptions='-Djava.security.manager=allow' "
        "/opt/spark-jobs/trend_aggregation_job.py",
        "提交趋势聚合作业")

    # ========================================
    # 完成
    # ========================================
    print("\n" + "=" * 60)
    print("  数据管道执行完成!")
    print("=" * 60)
    print("\n后续步骤:")
    print("  1. 启动后端: cd backend && uv run uvicorn app.main:app --reload --port 8000")
    print("  2. 启动前端: cd frontend && npm run dev")
    print("  3. 访问: http://localhost:3000")


if __name__ == "__main__":
    main()
