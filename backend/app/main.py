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
