from fastapi import APIRouter, Query
from typing import Optional
from backend.app.core.hbase_service import hbase_service
from backend.app.core.es_service import es_service

router = APIRouter()


def _merge_product_and_analysis(products: list, analyses: list) -> list:
    """将商品基础信息和Spark分析结果合并"""
    analysis_map = {a['product_id']: a for a in analyses}
    merged = []
    for p in products:
        pid = p['product_id']
        a = analysis_map.get(pid, {})
        merged.append({
            **p,
            'hot_score': a.get('hot_score', 0),
            'review_count': a.get('review_count', 0),
            'avg_rating': a.get('avg_rating', 0),
            'positive_rate': a.get('positive_rate', 0),
            'negative_rate': a.get('negative_rate', 0),
            'monthly_growth': a.get('monthly_growth', 0),
            'total_sales': a.get('total_sales', 0),
            'top_tags': a.get('top_tags', ''),
            'sales_trend': a.get('sales_trend', ''),
        })
    return merged


@router.get("/hot")
async def get_hot_products(
    category: Optional[str] = Query(None, description="品类筛选"),
    limit: int = Query(10, description="返回数量"),
    page: int = Query(1, description="页码")
):
    """获取爆款商品列表（商品信息 + Spark计算的分析指标）"""
    try:
        # 获取商品基础信息
        if category:
            products = hbase_service.get_products_by_category(category, 1000)
        else:
            products = hbase_service.get_all_products()

        # 获取分析结果
        analyses = hbase_service.get_all_product_analysis()

        # 合并
        merged = _merge_product_and_analysis(products, analyses)

        # 按爆款指数排序
        merged.sort(key=lambda x: x['hot_score'], reverse=True)

        # 分页
        total = len(merged)
        start = (page - 1) * limit
        end = start + limit
        paginated = merged[start:end]

        return {
            "code": 200,
            "message": "success",
            "data": {
                "products": paginated,
                "total": total,
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
        if product_id:
            reviews = hbase_service.get_reviews_by_product(product_id)
        elif category:
            products = hbase_service.get_products_by_category(category, 20)
            reviews = []
            for product in products:
                product_reviews = hbase_service.get_reviews_by_product(product['product_id'])
                reviews.extend(product_reviews)
        else:
            reviews = hbase_service.get_all_reviews()

        keyword_count = {}
        for review in reviews:
            content = review.get('content', '')
            for word in ['质量', '物流', '客服', '价格', '外观', '功能', '包装', '售后']:
                if word in content:
                    keyword_count[word] = keyword_count.get(word, 0) + 1

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
