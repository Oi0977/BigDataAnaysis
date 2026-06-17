from fastapi import APIRouter, Query
from typing import Optional
from backend.app.core.hbase_service import hbase_service
from backend.app.core.nlp_service import nlp_service
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
            reviews = hbase_service.get_all_reviews()

        # 使用 NLP 重新分析关键词和情感
        for review in reviews:
            # 用 jieba 重新提取关键词
            review['keywords'] = nlp_service.extract_keywords(review['content'])
            # 用 SnowNLP 重新做情感分析
            review['sentiment'] = nlp_service.analyze_sentiment(review['content'])

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

        total = len(reviews) if reviews else 1
        return {
            "code": 200,
            "message": "success",
            "data": {
                "totalReviews": len(reviews),
                "highFreqKeywords": high_freq_keywords,
                "sentimentDistribution": dict(sentiment_counter),
                "ratingDistribution": dict(rating_counter),
                "topComplaints": [
                    {"keyword": kw, "count": cnt, "percentage": round(cnt / total * 100, 1)}
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
