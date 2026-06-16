# 抖音电商竞品智能分析与AI素材工厂

一站式竞品智能分析与AI广告素材生成服务，解决商家"不知道竞品什么卖得好、不知道文案怎么写、不知道产品卖点怎么优化"三大痛点。

## 技术栈

- **前端：** Vue3 + ECharts
- **后端：** FastAPI + Python 3.11
- **大数据：** Kafka + Spark + HDFS + HBase + Elasticsearch
- **部署：** Docker + Docker Compose
- **包管理：** uv

## 快速开始

### 1. 启动服务

```bash
make build
make up
```

### 2. 生成测试数据

```bash
make mock-data
make init-data
```

### 3. 访问应用

- 前端：http://localhost
- 后端API：http://localhost:8000/docs

## 功能模块

1. **数据监控大屏** - 实时展示爬取量、品类分布、爆款统计
2. **爆款分析** - 分析爆款商品，计算爆款指数
3. **差评分析** - 分析差评高频词，生成痛点报告
4. **卖点推荐** - 基于竞品差评，反向生成产品优化卖点
5. **相似爆款检索** - ES语义检索，找到最相关的参考爆款
6. **AI文案生成** - 大模型参考爆款文案，生成专属广告文案

## 项目结构

```
BigHomework/
├── frontend/          # 前端项目
├── backend/           # 后端项目
├── spark-jobs/        # Spark作业
├── mock-data/         # Mock数据
├── docker-compose.yml # Docker编排
├── Makefile          # 构建命令
└── docs/             # 文档
```

## 开发指南

### 环境准备

1. 安装Docker Desktop
2. 安装uv（Python包管理器）
3. 安装Node.js（前端开发）

### 后端开发

```bash
cd backend

# 创建虚拟环境
uv venv --python 3.11

# 激活虚拟环境
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 安装依赖
uv sync

# 运行后端
uv run uvicorn app.main:app --reload
```

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 运行前端
npm run dev
```

### 运行测试

```bash
# 使用Makefile
make test

# 或者手动运行
cd backend
uv run pytest tests/ -v
```

## Docker部署

### 服务列表

| 服务 | 端口 | 说明 |
|------|------|------|
| frontend | 80 | Vue3前端 |
| backend | 8000 | FastAPI后端 |
| kafka | 9092 | 消息队列 |
| spark-master | 7077, 8080 | Spark主节点 |
| spark-worker | 8081 | Spark工作节点 |
| hdfs-namenode | 9870, 9000 | HDFS主节点 |
| hdfs-datanode | 9864 | HDFS数据节点 |
| hbase-master | 16010, 16000 | HBase主节点 |
| hbase-regionserver | 16020, 16030 | HBase区域服务器 |
| zookeeper | 2181 | Zookeeper |
| elasticsearch | 9200, 9300 | 搜索引擎 |

### 常用命令

```bash
# 启动所有服务
make up

# 停止所有服务
make down

# 查看日志
make logs

# 构建镜像
make build
```

## 数据来源

本项目使用Mock数据进行演示，包含：
- 100+商品数据
- 300+差评数据
- 覆盖8个品类

## 创新点

1. **双维度竞品分析** - 不仅分析爆款好在哪里，更分析竞品差在哪里
2. **反向卖点提炼** - 从竞品差评中挖掘用户痛点，转化为自身产品卖点
3. **完整大数据链路** - 采集→缓冲→计算→存储→检索→应用→可视化全链路打通
4. **AI + 大数据融合** - 大数据提供洞察，AI提供生成能力，二者深度结合
5. **真实商业价值** - 场景贴近实际，中小商家真能用得上

## 许可证

MIT License
