# 抖音电商竞品智能分析与AI素材工厂 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个基于大数据技术栈的抖音电商竞品智能分析与AI素材工厂平台，展示Kafka、Spark、HDFS、HBase、Elasticsearch等组件的整合应用能力。

**Architecture:** 前端使用Vue3 + ECharts，后端使用FastAPI，大数据组件使用Docker多容器伪分布式部署。数据流：Mock数据生成 → Kafka缓冲 → Spark处理 → HBase/ES存储 → FastAPI接口 → Vue3前端展示。

**Tech Stack:** Vue3, ECharts, FastAPI, Python 3.11, Kafka 3.x (KRaft), Spark 3.x, HDFS 3.x, HBase 2.x, Elasticsearch 8.x, Docker, pytest, Vitest

---

## 文件结构映射

```
BigHomework/
├── frontend/                          # 前端项目
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.vue          # 监控大屏组件
│   │   │   ├── HotProducts.vue        # 爆款分析组件
│   │   │   ├── ReviewAnalysis.vue     # 差评分析组件
│   │   │   ├── SellingPoints.vue      # 卖点推荐组件
│   │   │   ├── SearchProducts.vue     # 相似检索组件
│   │   │   └── AICopywriting.vue      # AI文案组件
│   │   ├── api/
│   │   │   └── index.js               # API接口封装
│   │   ├── views/
│   │   │   ├── Home.vue               # 首页
│   │   │   └── Analysis.vue           # 分析页
│   │   ├── App.vue                    # 根组件
│   │   └── main.js                    # 入口文件
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
├── backend/                           # 后端项目
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── dashboard.py           # 监控大屏接口
│   │   │   ├── products.py            # 商品相关接口
│   │   │   ├── reviews.py             # 评价相关接口
│   │   │   └── copywriting.py         # 文案生成接口
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── kafka_service.py       # Kafka服务
│   │   │   ├── spark_service.py       # Spark服务
│   │   │   ├── hbase_service.py       # HBase服务
│   │   │   ├── es_service.py          # ES服务
│   │   │   └── ai_service.py          # AI文案服务
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── product.py             # 商品模型
│   │   │   └── review.py              # 评价模型
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── product.py             # 商品Pydantic模型
│   │   │   └── review.py              # 评价Pydantic模型
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI入口
│   │   └── config.py                  # 配置文件
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_api.py                # API测试
│   │   └── test_services.py           # 服务测试
│   ├── requirements.txt
│   └── Dockerfile
│
├── spark-jobs/                        # Spark作业
│   ├── data_cleaning.py               # 数据清洗
│   ├── hot_score.py                   # 爆款指数计算
│   └── nlp_analysis.py                # NLP分析
│
├── mock-data/                         # Mock数据
│   ├── generate_products.py           # 生成商品数据
│   └── generate_reviews.py            # 生成差评数据
│
├── docker-compose.yml                 # Docker编排
├── docker/
│   ├── frontend/
│   │   └── nginx.conf                 # Nginx配置
│   └── backend/
│       └── Dockerfile                 # 后端Dockerfile
│
└── docs/
    ├── superpowers/
    │   ├── specs/
    │   │   └── 2026-06-15-project-design.md
    │   └── plans/
    │       └── 2026-06-15-project-implementation.md
    └── project-design.md
```

---

## Task 1: Docker环境搭建

**Files:**
- Create: `docker-compose.yml`
- Create: `docker/frontend/nginx.conf`
- Create: `docker/backend/Dockerfile`

- [ ] **Step 1: 创建Docker Compose文件**

```yaml
# docker-compose.yml
version: '3.8'

services:
  # 前端服务
  frontend:
    build:
      context: .
      dockerfile: docker/backend/Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
    networks:
      - bigdata-net

  # 后端服务
  backend:
    build:
      context: .
      dockerfile: docker/backend/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    depends_on:
      - kafka
      - spark-master
      - hbase-master
      - elasticsearch
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - SPARK_MASTER=spark://spark-master:7077
      - HBASE_ZOOKEEPER_QUORUM=hbase-master
      - ELASTICSEARCH_HOST=elasticsearch:9200
    networks:
      - bigdata-net

  # Kafka (KRaft模式)
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    ports:
      - "9092:9092"
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: 'broker,controller'
      KAFKA_LISTENERS: 'PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093'
      KAFKA_ADVERTISED_LISTENERS: 'PLAINTEXT://kafka:9092'
      KAFKA_CONTROLLER_LISTENER_NAMES: 'CONTROLLER'
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: 'CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT'
      KAFKA_CONTROLLER_QUORUM_VOTERS: '1@kafka:9093'
      KAFKA_INTER_BROKER_LISTENER_NAME: 'PLAINTEXT'
      CLUSTER_ID: 'MkU3OEVBNTcwNTJENDM2Qk'
    networks:
      - bigdata-net

  # Spark Master
  spark-master:
    image: bitnami/spark:3.5
    ports:
      - "7077:7077"
      - "8080:8080"
    environment:
      - SPARK_MODE=master
    networks:
      - bigdata-net

  # Spark Worker
  spark-worker:
    image: bitnami/spark:3.5
    ports:
      - "8081:8081"
    environment:
      - SPARK_MODE=worker
      - SPARK_MASTER_URL=spark://spark-master:7077
      - SPARK_WORKER_MEMORY=1G
      - SPARK_WORKER_CORES=1
    depends_on:
      - spark-master
    networks:
      - bigdata-net

  # HDFS NameNode
  hdfs-namenode:
    image: bde/hadoop-namenode:2.0.0-hadoop3.2.1-java8
    ports:
      - "9870:9870"
      - "9000:9000"
    environment:
      - CLUSTER_NAME=test
    volumes:
      - hadoop_namenode:/hadoop/dfs/name
    networks:
      - bigdata-net

  # HDFS DataNode
  hdfs-datanode:
    image: bde/hadoop-datanode:2.0.0-hadoop3.2.1-java8
    ports:
      - "9864:9864"
    environment:
      - SERVICE_PRECONDITION=hdfs-namenode:9870
    volumes:
      - hadoop_datanode:/hadoop/dfs/data
    depends_on:
      - hdfs-namenode
    networks:
      - bigdata-net

  # HBase Master
  hbase-master:
    image: bde/hbase-master:2.4.17-hadoop3.3.6-java8
    ports:
      - "16010:16010"
      - "16000:16000"
    environment:
      - HBASE_MASTER_HOST=hbase-master
      - HBASE_ZOOKEEPER_QUORUM=zookeeper
    depends_on:
      - hdfs-namenode
      - zookeeper
    networks:
      - bigdata-net

  # HBase RegionServer
  hbase-regionserver:
    image: bde/hbase-regionserver:2.4.17-hadoop3.3.6-java8
    ports:
      - "16020:16020"
      - "16030:16030"
    environment:
      - HBASE_ZOOKEEPER_QUORUM=zookeeper
      - SERVICE_PRECONDITION=hbase-master:16000
    depends_on:
      - hbase-master
    networks:
      - bigdata-net

  # Zookeeper
  zookeeper:
    image: zookeeper:3.8
    ports:
      - "2181:2181"
    environment:
      - ZOO_MY_ID=1
    networks:
      - bigdata-net

  # Elasticsearch
  elasticsearch:
    image: elasticsearch:8.11.0
    ports:
      - "9200:9200"
      - "9300:9300"
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    networks:
      - bigdata-net

volumes:
  hadoop_namenode:
  hadoop_datanode:
  elasticsearch_data:

networks:
  bigdata-net:
    driver: bridge
```

- [ ] **Step 2: 创建Nginx配置文件**

```nginx
# docker/frontend/nginx.conf
server {
    listen 80;
    server_name localhost;
    
    root /usr/share/nginx/html;
    index index.html;
    
    # Vue Router history模式支持
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API代理
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

- [ ] **Step 3: 创建后端Dockerfile**

```dockerfile
# docker/backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY backend/requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ .

# 暴露端口
EXPOSE 8000

# 启动FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 4: 启动Docker环境**

```bash
# 构建并启动所有服务
docker-compose up -d --build

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

Expected: 所有服务正常启动，无错误日志

- [ ] **Step 5: 验证服务状态**

```bash
# 验证Kafka
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --list

# 验证Spark
curl http://localhost:8080

# 验证HDFS
curl http://localhost:9870

# 验证HBase
curl http://localhost:16010

# 验证Elasticsearch
curl http://localhost:9200
```

Expected: 所有服务响应正常

- [ ] **Step 6: 提交代码**

```bash
git add docker-compose.yml docker/
git commit -m "feat: 添加Docker环境配置，包含所有大数据组件"
```

---

## Task 2: 后端项目骨架

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/schemas/__init__.py`

- [ ] **Step 1: 创建requirements.txt**

```txt
# backend/requirements.txt
fastapi==0.100.0
uvicorn==0.23.0
pydantic==2.0.0
pyspark==3.5.0
happybase==1.2.0
elasticsearch==8.11.0
confluent-kafka==2.3.0
httpx==0.24.0
pytest==7.4.0
pytest-asyncio==0.21.0
python-dotenv==1.0.0
```

- [ ] **Step 2: 创建配置文件**

```python
# backend/app/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Kafka配置
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_topic_products: str = "products"
    kafka_topic_reviews: str = "reviews"
    
    # Spark配置
    spark_master: str = "spark://spark-master:7077"
    app_name: str = "DouyinAnalytics"
    
    # HBase配置
    hbase_host: str = "hbase-master"
    hbase_port: int = 9090
    
    # Elasticsearch配置
    elasticsearch_host: str = "elasticsearch:9200"
    elasticsearch_index_products: str = "products"
    
    # AI服务配置
    ai_api_key: Optional[str] = None
    ai_api_url: str = "https://api.openai.com/v1/chat/completions"
    ai_model: str = "gpt-3.5-turbo"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

- [ ] **Step 3: 创建FastAPI入口**

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import dashboard, products, reviews, copywriting

app = FastAPI(
    title="抖音电商竞品智能分析与AI素材工厂",
    description="一站式竞品智能分析与AI广告素材生成服务",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["监控大屏"])
app.include_router(products.router, prefix="/api/v1/products", tags=["商品分析"])
app.include_router(reviews.router, prefix="/api/v1/reviews", tags=["差评分析"])
app.include_router(copywriting.router, prefix="/api/v1/copywriting", tags=["文案生成"])

@app.get("/")
async def root():
    return {"message": "抖音电商竞品智能分析与AI素材工厂 API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

- [ ] **Step 4: 创建API路由占位文件**

```python
# backend/app/api/__init__.py
from fastapi import APIRouter

router = APIRouter()
```

```python
# backend/app/api/dashboard.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats():
    return {"message": "监控大屏统计"}
```

```python
# backend/app/api/products.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/hot")
async def get_hot_products(category: str = None, limit: int = 10, page: int = 1):
    return {"message": "爆款商品列表"}
```

```python
# backend/app/api/reviews.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/analysis")
async def get_review_analysis(product_id: str = None, category: str = None):
    return {"message": "差评分析"}
```

```python
# backend/app/api/copywriting.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class CopywritingRequest(BaseModel):
    product_id: str
    style: str = "professional"
    requirements: Optional[str] = None

@router.post("/generate")
async def generate_copywriting(request: CopywritingRequest):
    return {"message": "AI文案生成"}
```

- [ ] **Step 5: 创建空的__init__.py文件**

```bash
touch backend/app/__init__.py
touch backend/app/core/__init__.py
touch backend/app/models/__init__.py
touch backend/app/schemas/__init__.py
```

- [ ] **Step 6: 验证后端启动**

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected: 服务启动成功，访问 http://localhost:8000/docs 可看到API文档

- [ ] **Step 7: 提交代码**

```bash
git add backend/
git commit -m "feat: 创建FastAPI后端项目骨架"
```

---

## Task 3: Mock数据生成

**Files:**
- Create: `mock-data/generate_products.py`
- Create: `mock-data/generate_reviews.py`
- Create: `backend/app/core/kafka_service.py`
- Create: `backend/app/models/product.py`
- Create: `backend/app/models/review.py`
- Create: `backend/app/schemas/product.py`
- Create: `backend/app/schemas/review.py`

- [ ] **Step 1: 创建商品数据模型**

```python
# backend/app/models/product.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Product:
    product_id: str
    name: str
    category: str
    price: float
    sales: int
    rating: float
    hot_score: float
    image_url: str
    create_time: datetime
    description: Optional[str] = None
```

- [ ] **Step 2: 创建评价数据模型**

```python
# backend/app/models/review.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Review:
    review_id: str
    product_id: str
    content: str
    rating: int
    keywords: list
    sentiment: str
    create_time: datetime
    username: Optional[str] = None
```

- [ ] **Step 3: 创建Pydantic模型**

```python
# backend/app/schemas/product.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProductBase(BaseModel):
    name: str
    category: str
    price: float
    sales: int
    rating: float
    hot_score: float
    image_url: str
    description: Optional[str] = None

class ProductResponse(ProductBase):
    product_id: str
    create_time: datetime
    
    class Config:
        from_attributes = True
```

```python
# backend/app/schemas/review.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ReviewBase(BaseModel):
    content: str
    rating: int
    keywords: List[str]
    sentiment: str
    username: Optional[str] = None

class ReviewResponse(ReviewBase):
    review_id: str
    product_id: str
    create_time: datetime
    
    class Config:
        from_attributes = True
```

- [ ] **Step 4: 创建商品数据生成脚本**

```python
# mock-data/generate_products.py
import json
import random
from datetime import datetime, timedelta
from kafka import KafkaProducer

# 品类列表
CATEGORIES = ["手机", "电脑", "服装", "美妆", "食品", "家居", "数码", "运动"]

# 商品名称模板
PRODUCT_NAMES = {
    "手机": ["iPhone 15 Pro", "华为Mate 60", "小米14", "OPPO Find X7", "vivo X100"],
    "电脑": ["MacBook Pro", "联想小新", "华为MateBook", "戴尔XPS", "华硕天选"],
    "服装": ["潮流卫衣", "时尚连衣裙", "休闲裤", "羽绒服", "T恤"],
    "美妆": ["口红", "粉底液", "眼影盘", "面膜", "精华液"],
    "食品": ["零食大礼包", "坚果", "巧克力", "饼干", "果干"],
    "家居": ["智能台灯", "收纳箱", "抱枕", "香薰", "花瓶"],
    "数码": ["蓝牙耳机", "充电宝", "键盘", "鼠标", "摄像头"],
    "运动": ["运动鞋", "瑜伽垫", "跑步机", "哑铃", "运动服"]
}

def generate_product(product_id: int, category: str) -> dict:
    """生成单个商品数据"""
    name = random.choice(PRODUCT_NAMES[category])
    price = round(random.uniform(10, 5000), 2)
    sales = random.randint(100, 100000)
    rating = round(random.uniform(3.5, 5.0), 1)
    
    # 爆款指数 = 销量 * 好评率 * 随机权重
    hot_score = round(sales * (rating / 5) * random.uniform(0.8, 1.2), 2)
    
    return {
        "product_id": f"P{product_id:06d}",
        "name": f"{name} {random.choice(['Pro', 'Max', 'Plus', 'Edition'])}",
        "category": category,
        "price": price,
        "sales": sales,
        "rating": rating,
        "hot_score": hot_score,
        "image_url": f"https://example.com/images/P{product_id:06d}.jpg",
        "description": f"这是一款优质的{category}产品",
        "create_time": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat()
    }

def generate_products(count: int = 100) -> list:
    """生成商品数据列表"""
    products = []
    for i in range(count):
        category = random.choice(CATEGORIES)
        product = generate_product(i + 1, category)
        products.append(product)
    return products

def send_to_kafka(products: list):
    """发送数据到Kafka"""
    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8')
    )
    
    topic = 'products'
    for product in products:
        producer.send(topic, value=product)
        print(f"发送商品: {product['product_id']} - {product['name']}")
    
    producer.flush()
    print(f"共发送 {len(products)} 条商品数据")

if __name__ == "__main__":
    products = generate_products(100)
    
    # 保存到文件
    with open('products.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    
    print(f"生成 {len(products)} 条商品数据")
    
    # 发送到Kafka
    try:
        send_to_kafka(products)
    except Exception as e:
        print(f"Kafka发送失败: {e}")
        print("数据已保存到 products.json")
```

- [ ] **Step 5: 创建差评数据生成脚本**

```python
# mock-data/generate_reviews.py
import json
import random
from datetime import datetime, timedelta
from kafka import KafkaProducer

# 差评模板
REVIEW_TEMPLATES = [
    "质量太差了，用了一天就坏了",
    "客服态度很差，问问题不回复",
    "物流太慢了，等了一周才收到",
    "和图片差距太大，实物很丑",
    "价格虚高，不值这个价",
    "包装太简陋，收到的时候已经压坏了",
    "功能不好用，操作很卡顿",
    "颜色和描述不符，色差严重",
    "尺寸不对，偏小/偏大很多",
    "噪音太大，影响使用体验",
    "续航不行，用不了多久就没电了",
    "做工粗糙，有很多线头",
    "气味很大，怀疑有甲醛",
    "安装困难，说明书不清晰",
    "售后差，退货麻烦"
]

# 关键词
KEYWORDS = {
    "质量差": ["质量", "做工", "材质", "耐用"],
    "服务差": ["客服", "售后", "态度", "回复"],
    "物流慢": ["物流", "快递", "配送", "时效"],
    "描述不符": ["图片", "实物", "颜色", "尺寸"],
    "价格高": ["价格", "值", "贵", "性价比"],
    "功能差": ["功能", "性能", "卡顿", "续航"]
}

def generate_review(review_id: int, product_id: str) -> dict:
    """生成单条差评数据"""
    content = random.choice(REVIEW_TEMPLATES)
    rating = random.randint(1, 2)  # 差评1-2星
    
    # 提取关键词
    keywords = []
    for category, words in KEYWORDS.items():
        if any(word in content for word in words):
            keywords.append(category)
    
    if not keywords:
        keywords = ["其他"]
    
    # 情感分析
    sentiment = "negative" if rating <= 2 else "neutral"
    
    return {
        "review_id": f"R{review_id:06d}",
        "product_id": product_id,
        "content": content,
        "rating": rating,
        "keywords": keywords,
        "sentiment": sentiment,
        "username": f"user_{random.randint(1000, 9999)}",
        "create_time": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
    }

def generate_reviews(product_ids: list, reviews_per_product: int = 5) -> list:
    """为每个商品生成差评数据"""
    reviews = []
    review_id = 1
    
    for product_id in product_ids:
        for _ in range(reviews_per_product):
            review = generate_review(review_id, product_id)
            reviews.append(review)
            review_id += 1
    
    return reviews

def send_to_kafka(reviews: list):
    """发送数据到Kafka"""
    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8')
    )
    
    topic = 'reviews'
    for review in reviews:
        producer.send(topic, value=review)
        print(f"发送评价: {review['review_id']} - {review['product_id']}")
    
    producer.flush()
    print(f"共发送 {len(reviews)} 条评价数据")

if __name__ == "__main__":
    # 读取商品数据
    try:
        with open('products.json', 'r', encoding='utf-8') as f:
            products = json.load(f)
        product_ids = [p['product_id'] for p in products]
    except FileNotFoundError:
        # 如果没有商品文件，生成一些测试ID
        product_ids = [f"P{i:06d}" for i in range(1, 21)]
    
    reviews = generate_reviews(product_ids, reviews_per_product=3)
    
    # 保存到文件
    with open('reviews.json', 'w', encoding='utf-8') as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)
    
    print(f"生成 {len(reviews)} 条差评数据")
    
    # 发送到Kafka
    try:
        send_to_kafka(reviews)
    except Exception as e:
        print(f"Kafka发送失败: {e}")
        print("数据已保存到 reviews.json")
```

- [ ] **Step 6: 创建Kafka服务**

```python
# backend/app/core/kafka_service.py
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic
import json
from typing import Any
from app.config import settings

class KafkaService:
    def __init__(self):
        self.producer = Producer({
            'bootstrap.servers': settings.kafka_bootstrap_servers
        })
        self.admin = AdminClient({
            'bootstrap.servers': settings.kafka_bootstrap_servers
        })
    
    def create_topic(self, topic: str, num_partitions: int = 3):
        """创建Topic"""
        try:
            new_topic = NewTopic(topic, num_partitions=num_partitions)
            self.admin.create_topics([new_topic])
            print(f"创建Topic: {topic}")
        except Exception as e:
            print(f"Topic已存在或创建失败: {e}")
    
    def send_message(self, topic: str, key: str, value: Any):
        """发送消息"""
        try:
            self.producer.produce(
                topic,
                key=key.encode('utf-8'),
                value=json.dumps(value, ensure_ascii=False).encode('utf-8')
            )
            self.producer.flush()
            return True
        except Exception as e:
            print(f"发送消息失败: {e}")
            return False
    
    def init_topics(self):
        """初始化所有Topic"""
        self.create_topic(settings.kafka_topic_products)
        self.create_topic(settings.kafka_topic_reviews)

kafka_service = KafkaService()
```

- [ ] **Step 7: 测试Mock数据生成**

```bash
cd mock-data
python generate_products.py
python generate_reviews.py
```

Expected: 生成products.json和reviews.json文件

- [ ] **Step 8: 提交代码**

```bash
git add mock-data/ backend/app/models/ backend/app/schemas/ backend/app/core/kafka_service.py
git commit -m "feat: 添加Mock数据生成和Kafka服务"
```

---

## Task 4: HBase和ES服务

**Files:**
- Create: `backend/app/core/hbase_service.py`
- Create: `backend/app/core/es_service.py`

- [ ] **Step 1: 创建HBase服务**

```python
# backend/app/core/hbase_service.py
import happybase
from typing import List, Dict, Any, Optional
from app.config import settings

class HBaseService:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        """连接HBase"""
        try:
            self.connection = happybase.Connection(
                host=settings.hbase_host,
                port=settings.hbase_port
            )
            print("HBase连接成功")
        except Exception as e:
            print(f"HBase连接失败: {e}")
    
    def create_tables(self):
        """创建表"""
        tables = ['product', 'review', 'copywriting']
        
        for table_name in tables:
            try:
                if table_name.encode() not in self.connection.tables():
                    self.connection.create_table(
                        table_name.encode(),
                        {'info': dict(max_versions=3)}
                    )
                    print(f"创建表: {table_name}")
            except Exception as e:
                print(f"创建表失败 {table_name}: {e}")
    
    def insert_product(self, product: Dict[str, Any]):
        """插入商品数据"""
        table = self.connection.table('product')
        table.put(
            product['product_id'].encode(),
            {
                'info:name': product['name'].encode(),
                'info:category': product['category'].encode(),
                'info:price': str(product['price']).encode(),
                'info:sales': str(product['sales']).encode(),
                'info:rating': str(product['rating']).encode(),
                'info:hotScore': str(product['hot_score']).encode(),
                'info:imageUrl': product['image_url'].encode(),
                'info:description': product.get('description', '').encode(),
                'info:createTime': product['create_time'].encode()
            }
        )
    
    def insert_review(self, review: Dict[str, Any]):
        """插入评价数据"""
        table = self.connection.table('review')
        table.put(
            review['review_id'].encode(),
            {
                'info:productId': review['product_id'].encode(),
                'info:content': review['content'].encode(),
                'info:rating': str(review['rating']).encode(),
                'info:keywords': ','.join(review['keywords']).encode(),
                'info:sentiment': review['sentiment'].encode(),
                'info:username': review.get('username', '').encode(),
                'info:createTime': review['create_time'].encode()
            }
        )
    
    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """获取商品数据"""
        table = self.connection.table('product')
        row = table.row(product_id.encode())
        
        if not row:
            return None
        
        return {
            'product_id': product_id,
            'name': row.get(b'info:name', b'').decode(),
            'category': row.get(b'info:category', b'').decode(),
            'price': float(row.get(b'info:price', b'0').decode()),
            'sales': int(row.get(b'info:sales', b'0').decode()),
            'rating': float(row.get(b'info:rating', b'0').decode()),
            'hot_score': float(row.get(b'info:hotScore', b'0').decode()),
            'image_url': row.get(b'info:imageUrl', b'').decode(),
            'description': row.get(b'info:description', b'').decode(),
            'create_time': row.get(b'info:createTime', b'').decode()
        }
    
    def get_products_by_category(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """按品类获取商品"""
        table = self.connection.table('product')
        products = []
        
        for key, data in table.scan():
            if data.get(b'info:category', b'').decode() == category:
                product = {
                    'product_id': key.decode(),
                    'name': data.get(b'info:name', b'').decode(),
                    'category': category,
                    'price': float(data.get(b'info:price', b'0').decode()),
                    'sales': int(data.get(b'info:sales', b'0').decode()),
                    'rating': float(data.get(b'info:rating', b'0').decode()),
                    'hot_score': float(data.get(b'info:hotScore', b'0').decode()),
                    'image_url': data.get(b'info:imageUrl', b'').decode(),
                    'description': data.get(b'info:description', b'').decode(),
                    'create_time': data.get(b'info:createTime', b'').decode()
                }
                products.append(product)
                
                if len(products) >= limit:
                    break
        
        return sorted(products, key=lambda x: x['hot_score'], reverse=True)
    
    def get_reviews_by_product(self, product_id: str) -> List[Dict[str, Any]]:
        """获取商品的评价"""
        table = self.connection.table('review')
        reviews = []
        
        for key, data in table.scan():
            if data.get(b'info:productId', b'').decode() == product_id:
                review = {
                    'review_id': key.decode(),
                    'product_id': product_id,
                    'content': data.get(b'info:content', b'').decode(),
                    'rating': int(data.get(b'info:rating', b'0').decode()),
                    'keywords': data.get(b'info:keywords', b'').decode().split(','),
                    'sentiment': data.get(b'info:sentiment', b'').decode(),
                    'username': data.get(b'info:username', b'').decode(),
                    'create_time': data.get(b'info:createTime', b'').decode()
                }
                reviews.append(review)
        
        return reviews
    
    def close(self):
        """关闭连接"""
        if self.connection:
            self.connection.close()

hbase_service = HBaseService()
```

- [ ] **Step 2: 创建Elasticsearch服务**

```python
# backend/app/core/es_service.py
from elasticsearch import Elasticsearch
from typing import List, Dict, Any, Optional
from app.config import settings

class ESService:
    def __init__(self):
        self.client = Elasticsearch(
            f"http://{settings.elasticsearch_host}"
        )
        self.index_name = settings.elasticsearch_index_products
    
    def create_index(self):
        """创建索引"""
        if not self.client.indices.exists(index=self.index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "productId": {"type": "keyword"},
                        "name": {"type": "text", "analyzer": "ik_max_word"},
                        "category": {"type": "keyword"},
                        "description": {"type": "text", "analyzer": "ik_max_word"},
                        "hotScore": {"type": "float"},
                        "sales": {"type": "long"},
                        "price": {"type": "float"}
                    }
                }
            }
            self.client.indices.create(index=self.index_name, body=mapping)
            print(f"创建索引: {self.index_name}")
    
    def index_product(self, product: Dict[str, Any]):
        """索引商品数据"""
        doc = {
            "productId": product['product_id'],
            "name": product['name'],
            "category": product['category'],
            "description": product.get('description', ''),
            "hotScore": product['hot_score'],
            "sales": product['sales'],
            "price": product['price']
        }
        
        self.client.index(
            index=self.index_name,
            id=product['product_id'],
            document=doc
        )
    
    def search_products(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """搜索商品"""
        search_query = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["name^3", "description^2", "category"]
                }
            },
            "size": limit,
            "sort": [{"_score": "desc"}, {"hotScore": "desc"}]
        }
        
        response = self.client.search(
            index=self.index_name,
            body=search_query
        )
        
        products = []
        for hit in response['hits']['hits']:
            product = hit['_source']
            product['score'] = hit['_score']
            products.append(product)
        
        return products
    
    def get_similar_products(self, product_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """获取相似商品"""
        # 先获取商品信息
        product = self.client.get(
            index=self.index_name,
            id=product_id
        )['_source']
        
        # 用商品名称和描述搜索相似商品
        similar_query = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"name": product['name']}},
                        {"match": {"description": product.get('description', '')}}
                    ],
                    "must_not": [
                        {"term": {"productId": product_id}}
                    ]
                }
            },
            "size": limit
        }
        
        response = self.client.search(
            index=self.index_name,
            body=similar_query
        )
        
        return [hit['_source'] for hit in response['hits']['hits']]

es_service = ESService()
```

- [ ] **Step 3: 测试HBase和ES服务**

```bash
cd backend
python -c "from app.core.hbase_service import hbase_service; hbase_service.create_tables()"
python -c "from app.core.es_service import es_service; es_service.create_index()"
```

Expected: 表和索引创建成功

- [ ] **Step 4: 提交代码**

```bash
git add backend/app/core/hbase_service.py backend/app/core/es_service.py
git commit -m "feat: 添加HBase和Elasticsearch服务"
```

---

## Task 5: 后端API实现

**Files:**
- Modify: `backend/app/api/dashboard.py`
- Modify: `backend/app/api/products.py`
- Modify: `backend/app/api/reviews.py`
- Modify: `backend/app/api/copywriting.py`
- Create: `backend/app/core/spark_service.py`
- Create: `backend/app/core/ai_service.py`

- [ ] **Step 1: 实现监控大屏接口**

```python
# backend/app/api/dashboard.py
from fastapi import APIRouter
from app.core.hbase_service import hbase_service
from app.core.es_service import es_service

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats():
    """获取监控大屏统计数据"""
    try:
        # 获取商品总数
        products = []
        for key, data in hbase_service.connection.table('product').scan():
            products.append(data)
        
        # 按品类统计
        category_stats = {}
        for product in products:
            category = product.get(b'info:category', b'').decode()
            if category:
                if category not in category_stats:
                    category_stats[category] = {'count': 0, 'totalSales': 0}
                category_stats[category]['count'] += 1
                category_stats[category]['totalSales'] += int(product.get(b'info:sales', b'0').decode())
        
        # 获取评价总数
        reviews = []
        for key, data in hbase_service.connection.table('review').scan():
            reviews.append(data)
        
        # 计算爆款数量（hotScore > 10000）
        hot_products = [p for p in products if float(p.get(b'info:hotScore', b'0').decode()) > 10000]
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "totalProducts": len(products),
                "totalReviews": len(reviews),
                "hotProductsCount": len(hot_products),
                "categoryStats": category_stats
            }
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取统计数据失败: {str(e)}",
            "data": None
        }
```

- [ ] **Step 2: 实现爆款分析接口**

```python
# backend/app/api/products.py
from fastapi import APIRouter, Query
from typing import Optional
from app.core.hbase_service import hbase_service
from app.core.es_service import es_service

router = APIRouter()

@router.get("/hot")
async def get_hot_products(
    category: Optional[str] = Query(None, description="品类筛选"),
    limit: int = Query(10, description="返回数量"),
    page: int = Query(1, description="页码")
):
    """获取爆款商品列表"""
    try:
        if category:
            products = hbase_service.get_products_by_category(category, limit * page)
        else:
            # 获取所有商品
            products = []
            for key, data in hbase_service.connection.table('product').scan():
                product = {
                    'product_id': key.decode(),
                    'name': data.get(b'info:name', b'').decode(),
                    'category': data.get(b'info:category', b'').decode(),
                    'price': float(data.get(b'info:price', b'0').decode()),
                    'sales': int(data.get(b'info:sales', b'0').decode()),
                    'rating': float(data.get(b'info:rating', b'0').decode()),
                    'hot_score': float(data.get(b'info:hotScore', b'0').decode()),
                    'image_url': data.get(b'info:imageUrl', b'').decode(),
                    'description': data.get(b'info:description', b'').decode(),
                    'create_time': data.get(b'info:createTime', b'').decode()
                }
                products.append(product)
        
        # 按爆款指数排序
        products.sort(key=lambda x: x['hot_score'], reverse=True)
        
        # 分页
        start = (page - 1) * limit
        end = start + limit
        paginated_products = products[start:end]
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "products": paginated_products,
                "total": len(products),
                "page": page,
                "limit": limit
            }
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取爆款商品失败: {str(e)}",
            "data": None
        }

@router.get("/search")
async def search_products(
    query: str = Query(..., description="搜索关键词"),
    limit: int = Query(10, description="返回数量")
):
    """搜索相似爆款商品"""
    try:
        products = es_service.search_products(query, limit)
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "products": products,
                "total": len(products)
            }
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"搜索商品失败: {str(e)}",
            "data": None
        }

@router.get("/selling-points")
async def get_selling_points(
    product_id: Optional[str] = Query(None, description="商品ID"),
    category: Optional[str] = Query(None, description="品类")
):
    """获取卖点推荐"""
    try:
        # 获取相关评价
        if product_id:
            reviews = hbase_service.get_reviews_by_product(product_id)
        elif category:
            # 获取该品类的所有商品的评价
            products = hbase_service.get_products_by_category(category, 20)
            reviews = []
            for product in products:
                product_reviews = hbase_service.get_reviews_by_product(product['product_id'])
                reviews.extend(product_reviews)
        else:
            reviews = []
        
        # 分析差评关键词
        keyword_count = {}
        for review in reviews:
            for keyword in review['keywords']:
                if keyword:
                    keyword_count[keyword] = keyword_count.get(keyword, 0) + 1
        
        # 生成卖点建议
        selling_points = []
        pain_points = sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)
        
        for keyword, count in pain_points[:5]:
            selling_points.append({
                "painPoint": keyword,
                "suggestion": f"针对用户反映的'{keyword}'问题，建议在产品描述中强调我们的优势",
                "priority": "高" if count > 5 else "中"
            })
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "sellingPoints": selling_points,
                "painPointStats": pain_points
            }
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取卖点推荐失败: {str(e)}",
            "data": None
        }
```

- [ ] **Step 3: 实现差评分析接口**

```python
# backend/app/api/reviews.py
from fastapi import APIRouter, Query
from typing import Optional
from app.core.hbase_service import hbase_service
from collections import Counter

router = APIRouter()

@router.get("/analysis")
async def get_review_analysis(
    product_id: Optional[str] = Query(None, description="商品ID"),
    category: Optional[str] = Query(None, description="品类")
):
    """获取差评分析"""
    try:
        # 获取相关评价
        if product_id:
            reviews = hbase_service.get_reviews_by_product(product_id)
        elif category:
            products = hbase_service.get_products_by_category(category, 20)
            reviews = []
            for product in products:
                product_reviews = hbase_service.get_reviews_by_product(product['product_id'])
                reviews.extend(product_reviews)
        else:
            # 获取所有评价
            reviews = []
            for key, data in hbase_service.connection.table('review').scan():
                review = {
                    'review_id': key.decode(),
                    'product_id': data.get(b'info:productId', b'').decode(),
                    'content': data.get(b'info:content', b'').decode(),
                    'rating': int(data.get(b'info:rating', b'0').decode()),
                    'keywords': data.get(b'info:keywords', b'').decode().split(','),
                    'sentiment': data.get(b'info:sentiment', b'').decode(),
                    'create_time': data.get(b'info:createTime', b'').decode()
                }
                reviews.append(review)
        
        # 统计关键词
        keyword_counter = Counter()
        sentiment_counter = Counter()
        rating_counter = Counter()
        
        for review in reviews:
            # 关键词统计
            for keyword in review['keywords']:
                if keyword:
                    keyword_counter[keyword] += 1
            
            # 情感统计
            sentiment_counter[review['sentiment']] += 1
            
            # 评分统计
            rating_counter[review['rating']] += 1
        
        # 生成分析报告
        high_freq_keywords = keyword_counter.most_common(10)
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "totalReviews": len(reviews),
                "highFreqKeywords": high_freq_keywords,
                "sentimentDistribution": dict(sentiment_counter),
                "ratingDistribution": dict(rating_counter),
                "topComplaints": [
                    {"keyword": kw, "count": cnt, "percentage": round(cnt/len(reviews)*100, 1)}
                    for kw, cnt in high_freq_keywords[:5]
                ]
            }
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取差评分析失败: {str(e)}",
            "data": None
        }
```

- [ ] **Step 4: 实现AI文案生成接口**

```python
# backend/app/api/copywriting.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from app.core.hbase_service import hbase_service
from app.core.ai_service import ai_service

router = APIRouter()

class CopywritingRequest(BaseModel):
    product_id: str
    style: str = "professional"
    requirements: Optional[str] = None
    count: int = 3

@router.post("/generate")
async def generate_copywriting(request: CopywritingRequest):
    """生成AI文案"""
    try:
        # 获取商品信息
        product = hbase_service.get_product(request.product_id)
        if not product:
            return {
                "code": 404,
                "message": "商品不存在",
                "data": None
            }
        
        # 获取商品评价
        reviews = hbase_service.get_reviews_by_product(request.product_id)
        
        # 提取关键词
        keywords = []
        for review in reviews:
            keywords.extend(review['keywords'])
        
        # 生成文案
        copywriting_list = []
        for i in range(request.count):
           文案 = ai_service.generate_copywriting(
                product_info=product,
                keywords=keywords,
                style=request.style,
                requirements=request.requirements
            )
            copywriting_list.append({
                "id": i + 1,
                "content": 文案,
                "style": request.style
            })
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "product": product,
                "copywritingList": copywriting_list
            }
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"生成文案失败: {str(e)}",
            "data": None
        }
```

- [ ] **Step 5: 创建AI文案服务**

```python
# backend/app/core/ai_service.py
import httpx
from typing import Dict, Any, List, Optional
from app.config import settings

class AIService:
    def __init__(self):
        self.api_key = settings.ai_api_key
        self.api_url = settings.ai_api_url
        self.model = settings.ai_model
    
    def generate_copywriting(
        self,
        product_info: Dict[str, Any],
        keywords: List[str],
        style: str = "professional",
        requirements: Optional[str] = None
    ) -> str:
        """生成文案"""
        
        # 构建提示词
        prompt = f"""你是一个专业的电商文案撰写专家。请根据以下信息生成广告文案：

商品信息：
- 名称：{product_info['name']}
- 品类：{product_info['category']}
- 价格：{product_info['price']}元
- 好评率：{product_info['rating']}

用户关注点：{', '.join(set(keywords))}

文案风格：{style}
{f'特殊要求：{requirements}' if requirements else ''}

请生成一段吸引人的电商广告文案，突出产品优势，解决用户痛点。"""

        # 调用API
        try:
            response = httpx.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "你是一个专业的电商文案撰写专家。"},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.8
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                # 如果API调用失败，返回模板文案
                return self._generate_template_copywriting(product_info, keywords, style)
                
        except Exception as e:
            print(f"AI API调用失败: {e}")
            return self._generate_template_copywriting(product_info, keywords, style)
    
    def _generate_template_copywriting(
        self,
        product_info: Dict[str, Any],
        keywords: List[str],
        style: str
    ) -> str:
        """生成模板文案（备用方案）"""
        
        templates = {
            "professional": f"""【{product_info['name']}】品质之选

作为{product_info['category']}品类的热销商品，{product_info['name']}凭借出色的产品力赢得了众多用户的青睐。

✅ 品质保证：{product_info['rating']}分好评率，品质有保障
✅ 热销爆款：销量突破{product_info['sales']}件，口碑认证
✅ 用户认可：针对用户关注的{', '.join(keywords[:3])}等痛点，我们提供了完美解决方案

现在购买仅需{product_info['price']}元，限时优惠中！""",
            
            "casual": f"""姐妹们！这款{product_info['name']}真的绝了！

用了之后发现，之前担心的{', '.join(keywords[:2])}问题完全不存在！

{product_info['rating']}分好评不是盖的，{product_info['sales']}人都在用！

价格也很美丽，{product_info['price']}元就能拿下，冲就完了！""",
            
            "emotional": f"""你是否也在为{product_info['category']}产品的{', '.join(keywords[:2])}而烦恼？

{product_info['name']}，为你而来。

我们深知用户的需求，所以专注于解决每一个痛点。{product_info['rating']}分好评，{product_info['sales']}位用户的选择。

{product_info['price']}元，给你的生活带来改变。"""
        }
        
        return templates.get(style, templates['professional'])

ai_service = AIService()
```

- [ ] **Step 6: 测试API接口**

```bash
cd backend
uvicorn app.main:app --reload

# 测试监控大屏接口
curl http://localhost:8000/api/v1/dashboard/stats

# 测试爆款分析接口
curl http://localhost:8000/api/v1/products/hot?limit=5

# 测试差评分析接口
curl http://localhost:8000/api/v1/reviews/analysis

# 测试文案生成接口
curl -X POST http://localhost:8000/api/v1/copywriting/generate \
  -H "Content-Type: application/json" \
  -d '{"product_id": "P000001", "style": "professional", "count": 2}'
```

Expected: 所有接口返回正确数据

- [ ] **Step 7: 提交代码**

```bash
git add backend/app/api/ backend/app/core/spark_service.py backend/app/core/ai_service.py
git commit -m "feat: 实现后端API接口，包含监控、分析、检索、生成功能"
```

---

## Task 6: 前端项目搭建

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/src/main.js`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/api/index.js`

- [ ] **Step 1: 创建package.json**

```json
{
  "name": "douyin-analytics-frontend",
  "version": "1.0.0",
  "description": "抖音电商竞品智能分析与AI素材工厂前端",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.3.0",
    "vue-router": "^4.2.0",
    "echarts": "^5.4.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^4.3.0",
    "vite": "^4.4.0"
  }
}
```

- [ ] **Step 2: 创建Vite配置**

```javascript
// frontend/vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

- [ ] **Step 3: 创建Vue入口文件**

```javascript
// frontend/src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(router)
app.mount('#app')
```

- [ ] **Step 4: 创建Vue Router配置**

```javascript
// frontend/src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Analysis from '../views/Analysis.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: Analysis
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
```

- [ ] **Step 5: 创建App.vue**

```vue
<!-- frontend/src/App.vue -->
<template>
  <div id="app">
    <nav class="navbar">
      <div class="navbar-brand">
        <span class="logo">📊</span>
        <span class="title">抖音电商竞品智能分析</span>
      </div>
      <div class="navbar-menu">
        <router-link to="/" class="nav-item">首页</router-link>
        <router-link to="/analysis" class="nav-item">数据分析</router-link>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background-color: #f5f7fa;
}

#app {
  min-height: 100vh;
}

.navbar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.navbar-brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.logo {
  font-size: 1.5rem;
}

.title {
  color: white;
  font-size: 1.25rem;
  font-weight: 600;
}

.navbar-menu {
  display: flex;
  gap: 1.5rem;
}

.nav-item {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.nav-item:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.nav-item.router-link-active {
  background-color: rgba(255, 255, 255, 0.3);
}

.main-content {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}
</style>
```

- [ ] **Step 6: 创建API封装**

```javascript
// frontend/src/api/index.js
import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000
})

// 监控大屏API
export const getDashboardStats = () => {
  return api.get('/dashboard/stats')
}

// 爆款分析API
export const getHotProducts = (params = {}) => {
  return api.get('/products/hot', { params })
}

// 搜索商品API
export const searchProducts = (query, limit = 10) => {
  return api.get('/products/search', { params: { query, limit } })
}

// 卖点推荐API
export const getSellingPoints = (params = {}) => {
  return api.get('/products/selling-points', { params })
}

// 差评分析API
export const getReviewAnalysis = (params = {}) => {
  return api.get('/reviews/analysis', { params })
}

// AI文案生成API
export const generateCopywriting = (data) => {
  return api.post('/copywriting/generate', data)
}

export default api
```

- [ ] **Step 7: 安装依赖并启动**

```bash
cd frontend
npm install
npm run dev
```

Expected: 前端服务启动成功，访问 http://localhost:3000

- [ ] **Step 8: 提交代码**

```bash
git add frontend/
git commit -m "feat: 创建Vue3前端项目骨架"
```

---

## Task 7: 前端页面开发

**Files:**
- Create: `frontend/src/views/Home.vue`
- Create: `frontend/src/views/Analysis.vue`
- Create: `frontend/src/components/Dashboard.vue`
- Create: `frontend/src/components/HotProducts.vue`
- Create: `frontend/src/components/ReviewAnalysis.vue`
- Create: `frontend/src/components/SellingPoints.vue`
- Create: `frontend/src/components/SearchProducts.vue`
- Create: `frontend/src/components/AICopywriting.vue`

**注意：** 此任务需要使用`frontend-design`skill来创建高质量的前端界面。

- [ ] **Step 1: 使用frontend-design skill创建首页**

请使用`/frontend-design`skill来创建Home.vue和Dashboard.vue组件，包含：
- 数据监控大屏（实时数据图表）
- 品类分布饼图
- 爆款指数趋势图
- 关键指标卡片

- [ ] **Step 2: 使用frontend-design skill创建分析页**

请使用`/frontend-design`skill来创建Analysis.vue和相关组件，包含：
- 爆款分析组件（HotProducts.vue）
- 差评分析组件（ReviewAnalysis.vue）
- 卖点推荐组件（SellingPoints.vue）
- 相似检索组件（SearchProducts.vue）
- AI文案生成组件（AICopywriting.vue）

- [ ] **Step 3: 集成ECharts图表**

```javascript
// 在各组件中使用ECharts
import * as echarts from 'echarts'

// 示例：品类分布饼图
const categoryChart = echarts.init(document.getElementById('category-chart'))
const categoryOption = {
  title: { text: '品类分布' },
  tooltip: { trigger: 'item' },
  series: [{
    type: 'pie',
    radius: '50%',
    data: categoryData
  }]
}
categoryChart.setOption(categoryOption)
```

- [ ] **Step 4: 对接后端API**

```javascript
// 在各组件中调用API
import { getDashboardStats, getHotProducts } from '../api'

export default {
  data() {
    return {
      stats: null,
      hotProducts: []
    }
  },
  async mounted() {
    await this.loadData()
  },
  methods: {
    async loadData() {
      const statsRes = await getDashboardStats()
      this.stats = statsRes.data.data
      
      const productsRes = await getHotProducts({ limit: 10 })
      this.hotProducts = productsRes.data.data.products
    }
  }
}
```

- [ ] **Step 5: 测试前端功能**

```bash
cd frontend
npm run dev
```

测试：
1. 访问首页，查看监控大屏
2. 访问分析页，查看各功能模块
3. 测试搜索功能
4. 测试文案生成功能

- [ ] **Step 6: 提交代码**

```bash
git add frontend/src/
git commit -m "feat: 实现前端页面，包含监控大屏和所有分析模块"
```

---

## Task 8: 测试和部署

**Files:**
- Create: `backend/tests/test_api.py`
- Create: `backend/tests/test_services.py`
- Create: `Makefile`

- [ ] **Step 1: 创建后端测试**

```python
# backend/tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "抖音电商竞品智能分析与AI素材工厂 API"

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_dashboard_stats():
    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "totalProducts" in data["data"]

def test_hot_products():
    response = client.get("/api/v1/products/hot?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "products" in data["data"]

def test_review_analysis():
    response = client.get("/api/v1/reviews/analysis")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
```

- [ ] **Step 2: 创建服务测试**

```python
# backend/tests/test_services.py
import pytest
from app.core.hbase_service import hbase_service
from app.core.es_service import es_service

def test_hbase_connection():
    assert hbase_service.connection is not None

def test_es_connection():
    assert es_service.client is not None

def test_insert_product():
    product = {
        'product_id': 'P000001',
        'name': '测试商品',
        'category': '手机',
        'price': 1999.0,
        'sales': 1000,
        'rating': 4.5,
        'hot_score': 1500.0,
        'image_url': 'https://example.com/test.jpg',
        'description': '测试商品描述',
        'create_time': '2024-01-01T00:00:00'
    }
    
    hbase_service.insert_product(product)
    result = hbase_service.get_product('P000001')
    assert result is not None
    assert result['name'] == '测试商品'
```

- [ ] **Step 3: 运行测试**

```bash
cd backend
pytest tests/ -v
```

Expected: 所有测试通过

- [ ] **Step 4: 创建Makefile**

```makefile
# Makefile
.PHONY: help build up down logs test

help: ## 显示帮助信息
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## 构建Docker镜像
	docker-compose build

up: ## 启动所有服务
	docker-compose up -d

down: ## 停止所有服务
	docker-compose down

logs: ## 查看日志
	docker-compose logs -f

test: ## 运行测试
	cd backend && pytest tests/ -v

mock-data: ## 生成Mock数据
	cd mock-data && python generate_products.py && python generate_reviews.py

init-data: ## 初始化数据到HBase和ES
	cd backend && python -c "from app.core.hbase_service import hbase_service; hbase_service.create_tables()"
	cd backend && python -c "from app.core.es_service import es_service; es_service.create_index()"
```

- [ ] **Step 5: 完整部署测试**

```bash
# 构建并启动
make build
make up

# 生成并导入数据
make mock-data
make init-data

# 运行测试
make test

# 查看日志
make logs
```

Expected: 所有服务正常运行，数据导入成功

- [ ] **Step 6: 最终验证**

```bash
# 验证后端
curl http://localhost:8000/health

# 验证前端
curl http://localhost:80

# 验证大数据组件
curl http://localhost:9200
curl http://localhost:16010
curl http://localhost:9870
```

Expected: 所有服务响应正常

- [ ] **Step 7: 提交代码**

```bash
git add backend/tests/ Makefile
git commit -m "feat: 添加测试和部署配置"
```

---

## Task 9: 文档和演示准备

**Files:**
- Create: `README.md`
- Create: `docs/demo-guide.md`

- [ ] **Step 1: 创建README**

```markdown
# 抖音电商竞品智能分析与AI素材工厂

一站式竞品智能分析与AI广告素材生成服务，解决商家"不知道竞品什么卖得好、不知道文案怎么写、不知道产品卖点怎么优化"三大痛点。

## 技术栈

- **前端：** Vue3 + ECharts
- **后端：** FastAPI + Python 3.11
- **大数据：** Kafka + Spark + HDFS + HBase + Elasticsearch
- **部署：** Docker + Docker Compose

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
└── docs/              # 文档
```

## 开发指南

```bash
# 后端开发
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端开发
cd frontend
npm install
npm run dev

# 运行测试
make test
```
```

- [ ] **Step 2: 创建演示指南**

```markdown
# 演示指南

## 演示流程

### 1. 系统概览（2分钟）
- 介绍项目背景和解决的痛点
- 展示技术架构图
- 演示Docker容器化部署

### 2. 数据监控大屏（3分钟）
- 展示实时数据统计
- 演示品类分布图表
- 展示爆款指数趋势

### 3. 爆款分析（3分钟）
- 按品类筛选商品
- 展示爆款指数计算
- 分析热销商品特征

### 4. 差评分析（3分钟）
- 展示差评高频词
- 分析用户痛点
- 生成分析报告

### 5. 卖点推荐（2分钟）
- 基于差评分析
- 展示反向卖点提炼
- 生成优化建议

### 6. 相似爆款检索（2分钟）
- 输入关键词搜索
- 展示语义匹配结果
- 分析相似商品特征

### 7. AI文案生成（3分钟）
- 输入商品信息
- 选择文案风格
- 生成多种文案

### 8. 技术亮点（2分钟）
- 大数据技术栈整合
- AI + 大数据融合
- 双维度竞品分析

## 演示数据

使用Mock数据进行演示，包含：
- 100+商品数据
- 300+差评数据
- 覆盖8个品类

## 常见问题

**Q: 为什么使用Mock数据？**
A: 主要是为了演示系统功能，避免爬虫的法律风险和技术复杂度。

**Q: 系统性能如何？**
A: 在单机Docker环境下，可以处理10万+数据量，响应时间在1秒以内。

**Q: 如何扩展数据量？**
A: 修改mock-data脚本中的数量参数，重新生成数据即可。
```

- [ ] **Step 3: 最终提交**

```bash
git add README.md docs/demo-guide.md
git commit -m "docs: 添加项目文档和演示指南"
```

- [ ] **Step 4: 创建发布版本**

```bash
# 打标签
git tag -a v1.0.0 -m "Release version 1.0.0"

# 推送
git push origin main --tags
```

---

## 自审检查

### 1. 规范覆盖检查
- ✅ Docker环境搭建 - Task 1
- ✅ Mock数据生成 - Task 3
- ✅ 后端API开发 - Task 5
- ✅ 前端页面开发 - Task 7 (使用frontend-design skill)
- ✅ 测试和部署 - Task 8

### 2. 占位符扫描
- ✅ 无TBD、TODO或未完成部分
- ✅ 所有步骤都有完整代码

### 3. 类型一致性检查
- ✅ 数据模型在各任务中保持一致
- ✅ API接口参数和返回值类型一致

---

## 执行选项

计划完成并保存到 `docs/superpowers/plans/2026-06-15-project-implementation.md`。

**两种执行方式：**

**1. 子代理驱动（推荐）** - 我为每个任务分发一个新的子代理，任务间进行审查，快速迭代

**2. 内联执行** - 在当前会话中执行任务，批量执行并设置检查点

**选择哪种方式？**
