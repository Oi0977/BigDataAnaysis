"""
商品分析计算脚本
读取原始数据（products + reviews + monthly_sales），计算分析指标，写入HBase。

功能等同于 Spark product_analysis_job.py，但使用纯Python实现，
适用于本地开发和课程演示。

计算指标:
  - hot_score: 爆款指数
  - positive_rate: 好评率
  - negative_rate: 差评率
  - review_count: 评价总数
  - avg_rating: 平均评分
  - monthly_growth: 月增长率
  - top_tags: 高频关键词

运行方式:
    cd 项目根目录
    uv run python scripts/compute_analysis.py
"""
import os
import sys
import json
from collections import Counter, defaultdict

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOCK_DIR = os.path.join(PROJECT_ROOT, "mock-data")
os.environ["RUN_MODE"] = "local"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def load_json(filename):
    """加载JSON文件"""
    path = os.path.join(MOCK_DIR, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_keywords(texts, top_n=10):
    """用jieba提取高频关键词"""
    try:
        import jieba
        stop_words = {
            '的', '了', '是', '在', '我', '有', '和', '就', '不', '人',
            '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
            '你', '会', '着', '没有', '看', '好', '自己', '这', '他', '她',
            '们', '那', '被', '从', '把', '还', '没', '过', '来', '对',
            '为', '以', '与', '或', '但', '而', '又', '能', '可', '吗',
            '啊', '吧', '呢', '哦', '哈', '嗯', '呀', '哇', '嘛', '啦',
            '比较', '真的', '确实', '非常', '特别', '其实', '觉得', '感觉',
        }
        all_text = " ".join(texts)
        words = jieba.lcut(all_text)
        filtered = [w for w in words if len(w) > 1 and w not in stop_words]
        counter = Counter(filtered)
        return [w for w, _ in counter.most_common(top_n)]
    except ImportError:
        return []


def compute_monthly_sales(sales_data):
    """将日销量聚合为月度数据"""
    monthly = defaultdict(lambda: defaultdict(int))
    for s in sales_data:
        pid = s['product_id']
        month = s['date'][:7]
        monthly[pid][month] += s['daily_sales']
    return monthly


def compute_growth_rate(monthly_data, product_id):
    """计算月增长率"""
    months = sorted(monthly_data.get(product_id, {}).keys())
    if len(months) < 2:
        return 0.0
    current = monthly_data[product_id][months[-1]]
    previous = monthly_data[product_id][months[-2]]
    if previous == 0:
        return 0.0
    return round((current - previous) / previous * 100, 2)


def compute_analysis(products, reviews, monthly_sales):
    """计算所有商品的分析指标"""
    # 聚合日销量为月度
    monthly_data = compute_monthly_sales(monthly_sales)

    # 按商品聚合评价
    review_groups = defaultdict(list)
    for r in reviews:
        review_groups[r['product_id']].append(r)

    # 提取评价文本用于关键词提取
    all_texts = [r['content'] for r in reviews]

    # 计算每个商品的分析指标
    results = []
    for product in products:
        pid = product['product_id']
        category = product['category']

        # 评价指标
        product_reviews = review_groups.get(pid, [])
        review_count = len(product_reviews)
        if review_count > 0:
            ratings = [r['rating'] for r in product_reviews]
            avg_rating = round(sum(ratings) / len(ratings), 2)
            positive_count = sum(1 for r in ratings if r >= 4)
            negative_count = sum(1 for r in ratings if r <= 2)
            positive_rate = round(positive_count / review_count, 4)
            negative_rate = round(negative_count / review_count, 4)
        else:
            avg_rating = 0.0
            positive_rate = 0.0
            negative_rate = 0.0

        # 销量指标
        product_months = monthly_data.get(pid, {})
        total_sales = sum(product_months.values())
        months_sorted = sorted(product_months.keys())
        latest_month_sales = product_months.get(months_sorted[-1], 0) if months_sorted else 0
        last_month_sales = product_months.get(months_sorted[-2], 0) if len(months_sorted) >= 2 else 0

        # 月增长率
        monthly_growth = compute_growth_rate(monthly_data, pid)

        # 销量趋势（近12个月）
        sales_trend = [product_months.get(m, 0) for m in months_sorted[-12:]]

        # 关键词（从该商品的评价中提取）
        product_texts = [r['content'] for r in product_reviews]
        top_tags = extract_keywords(product_texts if product_texts else all_texts[:100])

        results.append({
            'product_id': pid,
            'category': category,
            'total_sales': total_sales,
            'latest_month_sales': latest_month_sales,
            'last_month_sales': last_month_sales,
            'monthly_growth': monthly_growth,
            'review_count': review_count,
            'avg_rating': avg_rating,
            'positive_rate': positive_rate,
            'negative_rate': negative_rate,
            'top_tags': top_tags,
            'sales_trend': sales_trend,
        })

    # 按品类归一化计算爆款指数
    category_max = {}
    for r in results:
        cat = r['category']
        if cat not in category_max or r['total_sales'] > category_max[cat]:
            category_max[cat] = r['total_sales']

    for r in results:
        cat = r['category']
        max_sales = category_max.get(cat, 1)
        sales_score = r['total_sales'] / max_sales if max_sales > 0 else 0
        growth_score = min(max(r['monthly_growth'] / 100, 0), 1.0)
        rating_score = r['avg_rating'] / 5.0 if r['avg_rating'] > 0 else 0.7
        review_score = min(r['review_count'] / 500, 1.0)

        r['hot_score'] = round(
            (0.4 * sales_score + 0.3 * growth_score + 0.2 * rating_score + 0.1 * review_score) * 1000, 2
        )

    return results


def write_to_hbase(results):
    """将分析结果写入HBase"""
    try:
        import happybase
        print("\n[HBase] 连接 HBase (localhost:9090)...")
        conn = happybase.Connection('localhost', port=9090)

        # 确保表存在
        existing = conn.tables()
        if b'product_analysis' not in existing:
            conn.create_table('product_analysis', {
                'metrics': dict(max_versions=1),
                'trend': dict(max_versions=1),
            })
            print("[HBase] 创建表: product_analysis")

        table = conn.table('product_analysis')
        print(f"[HBase] 写入 {len(results)} 条分析结果...")

        with table.batch() as batch:
            for r in results:
                batch.put(r['product_id'].encode(), {
                    'metrics:hotScore': str(r['hot_score']).encode(),
                    'metrics:positiveRate': str(r['positive_rate']).encode(),
                    'metrics:negativeRate': str(r['negative_rate']).encode(),
                    'metrics:reviewCount': str(r['review_count']).encode(),
                    'metrics:avgRating': str(r['avg_rating']).encode(),
                    'metrics:monthlyGrowth': str(r['monthly_growth']).encode(),
                    'metrics:totalSales': str(r['total_sales']).encode(),
                    'metrics:topTags': json.dumps(r['top_tags'], ensure_ascii=False).encode(),
                    'trend:salesTrend': json.dumps(r['sales_trend']).encode(),
                })

        conn.close()
        print(f"[HBase] 成功写入 {len(results)} 条到 product_analysis 表")
    except Exception as e:
        print(f"[HBase] 写入失败: {e}")


def main():
    print("=" * 60)
    print("  商品分析计算脚本（纯Python版）")
    print("=" * 60)

    # 1. 加载数据
    print("\n--- 加载原始数据 ---")
    products = load_json('products.json')
    reviews = load_json('reviews.json')
    monthly_sales = load_json('monthly_sales.json')
    print(f"  商品: {len(products)} 条")
    print(f"  评价: {len(reviews)} 条")
    print(f"  日销量: {len(monthly_sales)} 条")

    # 2. 计算分析指标
    print("\n--- 计算分析指标 ---")
    results = compute_analysis(products, reviews, monthly_sales)
    print(f"  计算完成: {len(results)} 个商品")

    # 3. 写入HBase
    write_to_hbase(results)

    # 4. 打印Top10
    print("\n" + "=" * 60)
    print("  Top 10 热门商品（按爆款指数）")
    print("=" * 60)
    top10 = sorted(results, key=lambda x: x['hot_score'], reverse=True)[:10]
    for i, r in enumerate(top10, 1):
        name = next((p['name'] for p in products if p['product_id'] == r['product_id']), '')
        print(f"  {i:2d}. {r['product_id']} {name}")
        print(f"      品类: {r['category']} | 爆款指数: {r['hot_score']:.0f} | 评分: {r['avg_rating']}")
        print(f"      总销量: {r['total_sales']} | 好评率: {r['positive_rate']*100:.1f}% | 增长率: {r['monthly_growth']:.1f}%")
        print(f"      关键词: {', '.join(r['top_tags'][:5])}")

    # 5. 保存结果到JSON（备用）
    output_path = os.path.join(MOCK_DIR, 'product_analysis.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[完成] 分析结果已保存到: {output_path}")


if __name__ == "__main__":
    main()
