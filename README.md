# 基于大数据的电商竞品智能分析平台

一站式电商数据分析与洞察平台，帮助商家了解市场趋势、分析竞品表现、挖掘用户需求。

## 技术栈

- **前端：** Vue3 + ECharts
- **后端：** FastAPI + Python 3.12
- **大数据：** Kafka + Spark + HDFS + HBase + Elasticsearch
- **调度：** Apache Airflow（自动化数据管道）
- **部署：** Docker + Docker Compose
- **包管理：** uv

## 快速开始

### 1. 启动所有服务

```powershell
# 首次启动需要初始化 Airflow 数据库
docker compose up airflow-init

# 启动所有服务（包含 Airflow 调度器）
docker compose up -d
```

### 2. 访问应用

- **前端界面：** http://localhost
- **后端API：** http://localhost:8000/docs
- **Airflow 调度器：** http://localhost:8080（用户名/密码：airflow/airflow）

### 3. 手动触发一次数据管道

```powershell
# 方式1：通过 Airflow Web 界面
# 访问 http://localhost:8080，找到 douyin_etl_pipeline DAG，点击播放按钮

# 方式2：通过命令行
docker compose exec airflow-scheduler airflow dags trigger douyin_etl_pipeline
```

## 功能模块

1. **数据概览** - 实时展示商品数量、品类分布、销售趋势
2. **爆款分析** - 分析爆款商品，计算爆款指数
3. **差评分析** - 分析差评高频词，生成痛点报告
4. **趋势分析** - 月度销量趋势、品类增长趋势
5. **评价分析** - 情感分析、关键词提取、主题建模
6. **竞品对比** - 多维度竞品数据对比

## 项目结构

```
BigHomework/
├── frontend/          # 前端项目
├── backend/           # 后端项目
├── spark-jobs/        # Spark作业
├── scripts/           # 数据初始化等脚本
├── mock-data/         # Mock数据
├── dags/              # Airflow DAG 文件
├── docker/            # Docker配置文件
├── docker-compose.yml # Docker编排
└── docs/              # 文档
```

## 开发指南

### 环境准备

1. 安装 Docker Desktop
2. 安装 uv（Python包管理器）
3. 安装 Node.js（前端开发）

### 后端开发

```powershell
cd backend

# 创建虚拟环境
uv venv --python 3.12

# 激活虚拟环境
.venv\Scripts\activate

# 安装依赖
uv sync

# 运行后端
uv run uvicorn app.main:app --reload
```

### 前端开发

```powershell
cd frontend

# 安装依赖
npm install

# 运行前端
npm run dev
```

### 运行测试

```powershell
cd backend
uv run pytest tests/ -v
```

## Docker 部署

### 服务列表

| 服务 | 端口 | 说明 |
|------|------|------|
| frontend | 80 | Vue3前端 |
| backend | 8000 | FastAPI后端 |
| kafka | 9094 | 消息队列 |
| spark-master | 7077, 8081 | Spark主节点 |
| spark-worker | 8082 | Spark工作节点 |
| hdfs-namenode | 9870, 9000 | HDFS主节点 |
| hdfs-datanode | 9864 | HDFS数据节点 |
| hbase-master | 16010, 16000, 9090 | HBase主节点 |
| hbase-regionserver | 16020, 16030 | HBase区域服务器 |
| zookeeper | 2181 | Zookeeper |
| elasticsearch | 9200, 9300 | 搜索引擎 |
| postgres | 5432 | Airflow 元数据库 |
| redis | 6379 | Airflow 消息队列 |
| airflow-webserver | 8080 | Airflow Web界面 |
| airflow-scheduler | - | Airflow 调度器 |
| airflow-worker | - | Airflow 工作节点 |

### 常用命令

```powershell
# 启动所有服务
docker compose up -d

# 停止所有服务
docker compose down

# 停止并删除数据卷
docker compose down -v

# 查看容器状态
docker compose ps

# 查看某个服务日志
docker compose logs -f elasticsearch

# 重建某个服务
docker compose up -d --build elasticsearch

# 手动触发数据管道
docker compose exec airflow-scheduler airflow dags trigger douyin_etl_pipeline
```

## 自动化调度

项目使用 Apache Airflow 实现自动化数据管道：

- **调度频率：** 每天凌晨 2:00 自动执行
- **执行流程：** 生成数据 → 初始化存储 → 上传HDFS → Spark分析 → 计算指标
- **失败重试：** 3次，间隔5分钟
- **监控界面：** http://localhost:8080

## 数据来源

本项目使用 Mock 数据进行演示，包含：
- 100+ 商品数据
- 1000+ 评价数据
- 36000+ 日销量数据
- 覆盖 8 个品类

## 创新点

1. **完整大数据链路** - 采集 → 缓冲 → 计算 → 存储 → 检索 → 应用 → 可视化全链路打通
2. **AI + 大数据融合** - Spark进行大规模数据处理，NLP进行情感分析和关键词提取
3. **自动化调度** - Airflow实现定时自动执行，无需人工干预
4. **多维度分析** - 从商品、品类、时间等多个维度进行深度分析
5. **实时可视化** - ECharts实现数据实时展示，直观易懂

## 许可证

MIT License
