from fastapi import APIRouter, Query
from typing import Optional
from app.core.hbase_service import hbase_service
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
            # 获取所有评价
            reviews = []
            for key, data in hbase_service.connection.table('review').scan():
                review = {
                    'review_id': key.decode(),
                    'product_id': data.get(b'info:productId', b'').decode(),
                    'content': data.get(b'info:content', b'').decode(),
                    'rating': int(data.get(b'info:rating', b'0').decode()),
                    'keywords': data.get(b'info:keywords', b'').decode().split(','),
                    'sentiment': data.get(b'info:sentiment', b'').decode(),
                    'create_time': data.get(b'info:createTime', b'').decode()
                }
                reviews.append(review)

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

        return {
            "code": 200,
            "message": "success",
            "data": {
                "totalReviews": len(reviews),
                "highFreqKeywords": high_freq_keywords,
                "sentimentDistribution": dict(sentiment_counter),
                "ratingDistribution": dict(rating_counter),
                "topComplaints": [
                    {"keyword": kw, "count": cnt, "percentage": round(cnt/len(reviews)*100, 1)}
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
