import json
import os
from fastapi import APIRouter, Query
from typing import Optional
from backend.app.core.hbase_service import hbase_service
from backend.app.core.es_service import es_service

router = APIRouter()

_MOCK_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'mock-data')


def _load_json(filename):
    try:
        with open(os.path.join(_MOCK_DIR, filename), 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


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
            'daily_growth': a.get('daily_growth', 0),
            'weekly_growth': a.get('weekly_growth', 0),
            'total_sales': a.get('total_sales', 0),
            'top_tags': a.get('top_tags', ''),
            'sales_trend': a.get('sales_trend', ''),
            'score_breakdown': a.get('score_breakdown', {}),
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
        print(f"[爆款商品] HBase读取失败，尝试JSON fallback: {e}")
        # Fallback: 从本地JSON文件读取
        try:
            products = _load_json('products.json')
            analyses = _load_json('product_analysis.json')
            if category:
                products = [p for p in products if p.get('category') == category]
            merged = _merge_product_and_analysis(products, analyses)
            merged.sort(key=lambda x: x['hot_score'], reverse=True)
            total = len(merged)
            start = (page - 1) * limit
            paginated = merged[start:start + limit]
            return {"code": 200, "message": "success", "data": {"products": paginated, "total": total, "page": page, "limit": limit}}
        except Exception as e2:
            return {"code": 500, "message": f"获取爆款商品失败: {str(e2)}", "data": None}


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
        print(f"[搜索商品] ES读取失败，尝试JSON fallback: {e}")
        try:
            all_products = _load_json('products.json')
            results = [p for p in all_products if query in p.get('name', '') or query in p.get('description', '') or query in p.get('category', '')]
            return {"code": 200, "message": "success", "data": {"products": results[:limit], "total": len(results)}}
        except Exception as e2:
            return {"code": 500, "message": f"搜索商品失败: {str(e2)}", "data": None}


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

        # 每个痛点的具体卖点建议
        SUGGESTIONS = {
            '质量': {
                'suggestion': '在详情页突出品控流程（如出厂检测、质保承诺），用数据说话（如"通过10000次跌落测试"），打消用户对质量的顾虑',
                'example': '竞品差评高频词：做工粗糙、用料差、易损坏',
            },
            '物流': {
                'suggestion': '强调发货速度和物流保障（如"下单后24小时内发货"、"顺丰包邮"），在详情页标注预计到达时间',
                'example': '竞品差评高频词：发货慢、快递延误、包裹破损',
            },
            '客服': {
                'suggestion': '在商品描述中承诺客服响应时效（如"3分钟内回复"、"7天无理由退换"），提升用户购买信心',
                'example': '竞品差评高频词：回复慢、态度差、不解决问题',
            },
            '价格': {
                'suggestion': '突出性价比优势（如"同品质价格低30%"），或强调价值感（如"一套顶三套"），避免用户觉得不值',
                'example': '竞品差评高频词：价格虚高、不值这个价、性价比低',
            },
            '外观': {
                'suggestion': '用实拍图替代渲染图，展示多角度细节，标注真实尺寸和色差范围，降低预期落差',
                'example': '竞品差评高频词：色差大、与图片不符、做工粗糙',
            },
            '功能': {
                'suggestion': '在详情页用场景化演示说明核心功能（如GIF动图、对比视频），避免用户因不会用而差评',
                'example': '竞品差评高频词：功能不符宣传、操作复杂、性能不达标',
            },
            '包装': {
                'suggestion': '升级防震包装（如气泡柱、泡沫内衬），在详情页展示开箱实拍，承诺"破损包赔"',
                'example': '竞品差评高频词：包装简陋、运输压扁、配件遗漏',
            },
            '售后': {
                'suggestion': '在详情页醒目位置标注售后政策（如"30天无理由退换"、"质量问题免费寄回"），降低决策门槛',
                'example': '竞品差评高频词：退货难、保修拒绝、流程拖沓',
            },
        }

        selling_points = []
        pain_points = sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)

        for keyword, count in pain_points[:5]:
            info = SUGGESTIONS.get(keyword, {'suggestion': f'针对"{keyword}"问题优化产品描述', 'example': ''})
            selling_points.append({
                "painPoint": keyword,
                "suggestion": info['suggestion'],
                "example": info['example'],
                "mentionCount": count,
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
        print(f"[卖点推荐] HBase读取失败，尝试JSON fallback: {e}")
        try:
            reviews = _load_json('reviews.json')
            if category:
                products_data = _load_json('products.json')
                pids = {p['product_id'] for p in products_data if p.get('category') == category}
                reviews = [r for r in reviews if r.get('product_id') in pids]
            if product_id:
                reviews = [r for r in reviews if r.get('product_id') == product_id]

            keyword_count = {}
            for review in reviews:
                content = review.get('content', '')
                for word in ['质量', '物流', '客服', '价格', '外观', '功能', '包装', '售后']:
                    if word in content:
                        keyword_count[word] = keyword_count.get(word, 0) + 1

            pain_points = sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)
            SUGGESTIONS = {
                '质量': {'suggestion': '在详情页突出品控流程（如出厂检测、质保承诺），用数据说话', 'example': '竞品差评高频词：做工粗糙、用料差、易损坏'},
                '物流': {'suggestion': '强调发货速度和物流保障（如"下单后24小时内发货"、"顺丰包邮"）', 'example': '竞品差评高频词：发货慢、快递延误、包裹破损'},
                '客服': {'suggestion': '承诺客服响应时效（如"3分钟内回复"、"7天无理由退换"）', 'example': '竞品差评高频词：回复慢、态度差、不解决问题'},
                '价格': {'suggestion': '突出性价比优势（如"同品质价格低30%"），或强调价值感', 'example': '竞品差评高频词：价格虚高、不值这个价、性价比低'},
                '外观': {'suggestion': '用实拍图替代渲染图，展示多角度细节，标注真实尺寸和色差范围', 'example': '竞品差评高频词：色差大、与图片不符、做工粗糙'},
                '功能': {'suggestion': '用场景化演示说明核心功能（如GIF动图、对比视频）', 'example': '竞品差评高频词：功能不符宣传、操作复杂、性能不达标'},
                '包装': {'suggestion': '升级防震包装，展示开箱实拍，承诺"破损包赔"', 'example': '竞品差评高频词：包装简陋、运输压扁、配件遗漏'},
                '售后': {'suggestion': '醒目位置标注售后政策（如"30天无理由退换"、"质量问题免费寄回"）', 'example': '竞品差评高频词：退货难、保修拒绝、流程拖沓'},
            }
            selling_points = []
            for kw, cnt in pain_points[:5]:
                info = SUGGESTIONS.get(kw, {'suggestion': f'针对"{kw}"问题优化产品描述', 'example': ''})
                selling_points.append({"painPoint": kw, "suggestion": info['suggestion'], "example": info['example'], "mentionCount": cnt, "priority": "高" if cnt > 5 else "中"})
            return {"code": 200, "message": "success", "data": {"sellingPoints": selling_points, "painPointStats": pain_points}}
        except Exception as e2:
            return {"code": 500, "message": f"获取卖点推荐失败: {str(e2)}", "data": None}
