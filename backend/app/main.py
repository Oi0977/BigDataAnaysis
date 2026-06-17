import os
import sys

# 将项目根目录加入 sys.path（兼容从 backend/ 目录运行 uvicorn）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api import dashboard, products, reviews


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动和关闭事件"""
    print("应用启动中...")

    # 初始化 HBase
    try:
        from backend.app.core.hbase_service import hbase_service
        hbase_service.create_tables()
        print("HBase 表初始化完成")
    except Exception as e:
        print(f"HBase 初始化失败: {e}")

    # 初始化 Elasticsearch
    try:
        from backend.app.core.es_service import es_service
        es_service.create_index()
        print("ES 索引初始化完成")
    except Exception as e:
        print(f"ES 初始化失败: {e}")

    yield

    # 关闭时
    print("应用关闭中...")
    try:
        from backend.app.core.hbase_service import hbase_service
        hbase_service.close()
    except Exception:
        pass


app = FastAPI(
    title="抖音电商竞品智能分析与AI素材工厂",
    description="一站式竞品智能分析与AI广告素材生成服务",
    version="1.0.0",
    lifespan=lifespan
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


@app.get("/")
async def root():
    return {"message": "抖音电商竞品智能分析与AI素材工厂 API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
