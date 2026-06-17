from fastapi import APIRouter
from backend.app.core.hbase_service import hbase_service

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats():
    """获取监控大屏统计数据"""
    try:
        products = hbase_service.get_all_products()
        reviews = hbase_service.get_all_reviews()
        analyses = hbase_service.get_all_product_analysis()

        # 按品类统计
        category_stats = {}
        for product in products:
            category = product['category']
            if category:
                if category not in category_stats:
                    category_stats[category] = {'count': 0, 'totalSales': 0}
                category_stats[category]['count'] += 1

        # 从分析结果补充销量和爆款数
        hot_count = 0
        for a in analyses:
            cat = next((p['category'] for p in products if p['product_id'] == a['product_id']), '')
            if cat and cat in category_stats:
                category_stats[cat]['totalSales'] += a.get('total_sales', 0)
            if a.get('hot_score', 0) > 300:
                hot_count += 1

        return {
            "code": 200,
            "message": "success",
            "data": {
                "totalProducts": len(products),
                "totalReviews": len(reviews),
                "hotProductsCount": hot_count,
                "categoryStats": category_stats
            }
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取统计数据失败: {str(e)}",
            "data": None
        }


@router.get("/trend")
async def get_dashboard_trend():
    """获取爆款指数趋势数据（按月统计）"""
    try:
        products = hbase_service.get_all_products()

        monthly_data = {}
        for product in products:
            create_time = product.get('create_time', '')
            if create_time and len(create_time) >= 7:
                month = create_time[:7]
                if month not in monthly_data:
                    monthly_data[month] = {'count': 0, 'totalHotScore': 0}
                monthly_data[month]['count'] += 1

        sorted_months = sorted(monthly_data.keys(), reverse=True)[:6][::-1]

        return {
            "code": 200,
            "message": "success",
            "data": {
                "months": sorted_months,
                "hotScores": [round(monthly_data[m]['totalHotScore']) for m in sorted_months],
                "productCounts": [monthly_data[m]['count'] for m in sorted_months]
            }
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取趋势数据失败: {str(e)}",
            "data": None
        }
