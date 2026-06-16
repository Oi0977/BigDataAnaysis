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
