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
