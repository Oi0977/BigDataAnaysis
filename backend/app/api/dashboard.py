import json
import os
from fastapi import APIRouter
from backend.app.core.hbase_service import hbase_service

router = APIRouter()

_MOCK_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'mock-data')


def _load_json(filename):
    try:
        with open(os.path.join(_MOCK_DIR, filename), 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


@router.get("/stats")
async def get_dashboard_stats():
    """获取监控大屏统计数据"""
    try:
        products = hbase_service.get_all_products()
        reviews = hbase_service.get_all_reviews()
        analyses = hbase_service.get_all_product_analysis()

        category_stats = {}
        for product in products:
            category = product['category']
            if category:
                if category not in category_stats:
                    category_stats[category] = {'count': 0, 'totalSales': 0}
                category_stats[category]['count'] += 1

        hot_count = 0
        analysis_map = {a['product_id']: a for a in analyses}
        for p in products:
            cat = p['category']
            a = analysis_map.get(p['product_id'], {})
            if cat and cat in category_stats:
                category_stats[cat]['totalSales'] += a.get('total_sales', 0)
            if a.get('hot_score', 0) > 0.5:
                hot_count += 1

        return {"code": 200, "message": "success", "data": {
            "totalProducts": len(products), "totalReviews": len(reviews),
            "hotProductsCount": hot_count, "categoryStats": category_stats
        }}
    except Exception as e:
        print(f"[Dashboard] HBase读取失败，尝试JSON fallback: {e}")
        return {"code": 200, "message": "success", "data": _dashboard_stats_fallback()}


def _dashboard_stats_fallback():
    products = _load_json('products.json')
    reviews = _load_json('reviews.json')
    analyses = _load_json('product_analysis.json')
    category_stats = {}
    for p in products:
        cat = p.get('category', '')
        if cat:
            if cat not in category_stats:
                category_stats[cat] = {'count': 0, 'totalSales': 0}
            category_stats[cat]['count'] += 1
    analysis_map = {a['product_id']: a for a in analyses}
    hot_count = 0
    for p in products:
        cat = p.get('category', '')
        a = analysis_map.get(p['product_id'], {})
        if cat and cat in category_stats:
            category_stats[cat]['totalSales'] += a.get('total_sales', 0)
        if a.get('hot_score', 0) > 0.5:
            hot_count += 1
    return {"totalProducts": len(products), "totalReviews": len(reviews),
            "hotProductsCount": hot_count, "categoryStats": category_stats}


@router.get("/trend")
async def get_dashboard_trend():
    """获取爆款指数趋势数据"""
    try:
        products = hbase_service.get_all_products()
        analyses = hbase_service.get_all_product_analysis()
        analysis_map = {a['product_id']: a for a in analyses}

        monthly_data = {}
        for product in products:
            create_time = product.get('create_time', '')
            if create_time and len(create_time) >= 7:
                month = create_time[:7]
                if month not in monthly_data:
                    monthly_data[month] = {'count': 0, 'totalHotScore': 0}
                monthly_data[month]['count'] += 1
                a = analysis_map.get(product['product_id'], {})
                monthly_data[month]['totalHotScore'] += a.get('hot_score', 0)

        sorted_months = sorted(monthly_data.keys(), reverse=True)[:6][::-1]
        return {"code": 200, "message": "success", "data": {
            "months": sorted_months,
            "hotScores": [round(monthly_data[m]['totalHotScore'], 2) for m in sorted_months],
            "productCounts": [monthly_data[m]['count'] for m in sorted_months]
        }}
    except Exception as e:
        print(f"[Dashboard趋势] HBase读取失败，尝试JSON fallback: {e}")
        return {"code": 200, "message": "success", "data": _dashboard_trend_fallback()}


def _dashboard_trend_fallback():
    products = _load_json('products.json')
    analyses = _load_json('product_analysis.json')
    analysis_map = {a['product_id']: a for a in analyses}
    monthly_data = {}
    for p in products:
        ct = p.get('create_time', '')
        if ct and len(ct) >= 7:
            m = ct[:7]
            if m not in monthly_data:
                monthly_data[m] = {'count': 0, 'totalHotScore': 0}
            monthly_data[m]['count'] += 1
            a = analysis_map.get(p['product_id'], {})
            monthly_data[m]['totalHotScore'] += a.get('hot_score', 0)
    sorted_months = sorted(monthly_data.keys(), reverse=True)[:6][::-1]
    return {"months": sorted_months,
            "hotScores": [round(monthly_data[m]['totalHotScore'], 2) for m in sorted_months],
            "productCounts": [monthly_data[m]['count'] for m in sorted_months]}
