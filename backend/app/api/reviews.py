import json
import os
from fastapi import APIRouter, Query
from typing import Optional
from backend.app.core.hbase_service import hbase_service

router = APIRouter()

# JSON fallback 路径
_JSON_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'mock-data', 'review_analysis.json')


def _load_global_keywords():
    """从JSON文件读取全局差评关键词"""
    try:
        with open(_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data.get('globalKeywords', [])
        return []
    except Exception:
        return []


def _load_json_fallback():
    """从本地JSON文件加载预计算结果，兼容新旧格式"""
    try:
        with open(_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # 新格式: {"globalKeywords": [...], "products": [...]}
        if isinstance(data, dict) and 'products' in data:
            return data
        # 旧格式: [...]
        return {'globalKeywords': [], 'products': data}
    except Exception:
        return {'globalKeywords': [], 'products': []}


def _safe_json(raw, default=None):
    """安全解析JSON字符串"""
    if not raw:
        return default
    try:
        return json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return default


@router.get("/analysis")
async def get_review_analysis(
    product_id: Optional[str] = Query(None, description="商品ID"),
    category: Optional[str] = Query(None, description="品类")
):
    """获取差评分析（读取预计算结果，HBase不可用时fallback到JSON）"""
    try:
        if product_id:
            analysis = hbase_service.get_review_analysis(product_id)
            if not analysis:
                return {"code": 200, "message": "success", "data": _empty_data()}
            return {"code": 200, "message": "success", "data": _format_analysis(analysis)}

        # 按品类或全量聚合
        if category:
            products = hbase_service.get_products_by_category(category, 20)
            pids = [p['product_id'] for p in products]
        else:
            products = hbase_service.get_all_products()
            pids = [p['product_id'] for p in products]

        merged = _merge_analyses(pids)
        return {"code": 200, "message": "success", "data": merged}

    except Exception as e:
        print(f"[差评分析] HBase读取失败，尝试JSON fallback: {e}")
        # Fallback: 从本地JSON文件读取
        return {"code": 200, "message": "success", "data": _load_from_json(product_id, category)}


def _merge_analyses(product_ids: list) -> dict:
    """汇总多个商品的预计算分析结果（关键词用全局差评关键词）"""
    sentiment_total = {}
    rating_total = {}
    all_topic_dist = []
    all_topic_kw = []
    all_cluster_labels = {}
    all_cluster_kw = {}

    for pid in product_ids:
        a = hbase_service.get_review_analysis(pid)
        if not a:
            continue

        sent = _safe_json(a.get('sentiment_distribution', '{}'), {})
        for k, v in sent.items():
            sentiment_total[k] = sentiment_total.get(k, 0) + v

        rat = _safe_json(a.get('rating_distribution', '{}'), {})
        for k, v in rat.items():
            rating_total[k] = rating_total.get(k, 0) + v

        td = _safe_json(a.get('topic_distribution', '[]'), [])
        if td:
            all_topic_dist.append(td)

        tk = _safe_json(a.get('topic_keywords', '[]'), [])
        if tk and not all_topic_kw:
            all_topic_kw = tk

        cl = _safe_json(a.get('cluster_labels', '{}'), {})
        for k, v in cl.items():
            all_cluster_labels[k] = all_cluster_labels.get(k, 0) + v

        ck = _safe_json(a.get('cluster_keywords', '{}'), {})
        if ck and not all_cluster_kw:
            all_cluster_kw = ck

    avg_topic_dist = []
    if all_topic_dist:
        n = len(all_topic_dist)
        dim = len(all_topic_dist[0])
        avg_topic_dist = [round(sum(t[i] for t in all_topic_dist) / n, 6) for i in range(dim)]

    # 关键词用JSON文件中的全局差评关键词
    global_kw = _load_global_keywords()

    return {
        "totalReviews": sum(sentiment_total.values()),
        "highFreqKeywords": global_kw[:10],
        "sentimentDistribution": sentiment_total,
        "ratingDistribution": rating_total,
        "topComplaints": [
            {"keyword": kw['word'], "count": kw.get('count', 0), "percentage": 0}
            for kw in global_kw[:5]
        ],
        "topicDistribution": avg_topic_dist,
        "topicKeywords": all_topic_kw,
        "clusterLabels": all_cluster_labels,
        "clusterKeywords": all_cluster_kw,
        "tfidfKeywords": global_kw,
    }


def _format_analysis(a: dict) -> dict:
    """格式化单个商品的分析结果"""
    tfidf = _safe_json(a.get('keywords', a.get('tfidf_keywords', '[]')), [])
    sent = _safe_json(a.get('sentiment_distribution', '{}'), {})
    rat = _safe_json(a.get('rating_distribution', '{}'), {})
    td = _safe_json(a.get('topic_distribution', '[]'), [])
    tk = _safe_json(a.get('topic_keywords', '[]'), [])
    cl = _safe_json(a.get('cluster_labels', '{}'), {})
    ck = _safe_json(a.get('cluster_keywords', '{}'), {})

    return {
        "totalReviews": sum(sent.values()),
        "highFreqKeywords": [(kw.get('word', ''), kw.get('count', kw.get('score', 0))) if isinstance(kw, dict) else (kw, 0) for kw in tfidf[:10]],
        "sentimentDistribution": sent,
        "ratingDistribution": rat,
        "topComplaints": [
            {"keyword": kw.get('word', '') if isinstance(kw, dict) else kw, "count": kw.get('count', kw.get('score', 0)) if isinstance(kw, dict) else 0, "percentage": 0}
            for kw in tfidf[:5]
        ],
        "topicDistribution": td,
        "topicKeywords": tk,
        "clusterLabels": cl,
        "clusterKeywords": ck,
        "tfidfKeywords": tfidf,
    }


def _load_from_json(product_id=None, category=None):
    """从本地JSON文件加载数据并聚合"""
    fallback = _load_json_fallback()
    if not fallback or not isinstance(fallback, dict):
        return _empty_data()

    global_kw = fallback.get('globalKeywords', [])
    all_data = fallback.get('products', [])

    if not all_data:
        return _empty_data()

    # 按品类筛选
    if category:
        try:
            products = _load_products_json()
            pids = {p['product_id'] for p in products if p.get('category') == category}
            all_data = [d for d in all_data if d.get('product_id') in pids]
        except Exception:
            pass

    # 单品查询
    if product_id:
        item = next((d for d in all_data if d.get('product_id') == product_id), None)
        if item:
            return _format_analysis(item)
        return _empty_data()

    # 聚合所有数据
    sentiment_total = {}
    rating_total = {}
    all_topic_dist = []
    all_topic_kw = []
    all_cluster_labels = {}
    all_cluster_kw = {}

    for a in all_data:
        for k, v in a.get('sentiment_distribution', {}).items():
            sentiment_total[k] = sentiment_total.get(k, 0) + v
        for k, v in a.get('rating_distribution', {}).items():
            rating_total[k] = rating_total.get(k, 0) + v

        td = a.get('topic_distribution', [])
        if td:
            all_topic_dist.append(td)
        tk = a.get('topic_keywords', [])
        if tk and not all_topic_kw:
            all_topic_kw = tk

        for k, v in a.get('cluster_labels', {}).items():
            all_cluster_labels[k] = all_cluster_labels.get(k, 0) + v
        ck = a.get('cluster_keywords', {})
        if ck and not all_cluster_kw:
            all_cluster_kw = ck

    avg_topic_dist = []
    if all_topic_dist:
        n = len(all_topic_dist)
        dim = len(all_topic_dist[0])
        avg_topic_dist = [round(sum(t[i] for t in all_topic_dist) / n, 6) for i in range(dim)]

    return {
        "totalReviews": sum(sentiment_total.values()),
        "highFreqKeywords": global_kw[:10],
        "sentimentDistribution": sentiment_total,
        "ratingDistribution": rating_total,
        "topComplaints": [
            {"keyword": kw['word'], "count": kw.get('count', 0), "percentage": 0}
            for kw in global_kw[:5]
        ],
        "topicDistribution": avg_topic_dist,
        "topicKeywords": all_topic_kw,
        "clusterLabels": all_cluster_labels,
        "clusterKeywords": all_cluster_kw,
        "tfidfKeywords": global_kw,
    }


def _load_products_json():
    """加载商品JSON"""
    products_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'mock-data', 'products.json')
    with open(products_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _empty_data():
    """空数据默认值"""
    return {
        "totalReviews": 0,
        "highFreqKeywords": [],
        "sentimentDistribution": {},
        "ratingDistribution": {},
        "topComplaints": [],
        "topicDistribution": [],
        "topicKeywords": [],
        "clusterLabels": {},
        "clusterKeywords": {},
        "tfidfKeywords": [],
    }
