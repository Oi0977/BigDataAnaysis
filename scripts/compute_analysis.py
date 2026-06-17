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
  - weekly_growth: 周增长率（最近7天vs前7天）
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


def compute_daily_sales(sales_data):
    """按商品聚合日销量"""
    daily = defaultdict(lambda: defaultdict(int))
    for s in sales_data:
        daily[s['product_id']][s['date']] += s['daily_sales']
    return daily


def compute_growth_rate(daily_data, product_id):
    """计算日增长率和周增长率"""
    dates = sorted(daily_data.get(product_id, {}).keys())
    # 日增长率：最后一天 vs 倒数第二天
    daily_growth = 0.0
    if len(dates) >= 2:
        last = daily_data[product_id][dates[-1]]
        prev = daily_data[product_id][dates[-2]]
        if prev > 0:
            daily_growth = round((last - prev) / prev * 100, 2)
    # 周增长率：最近7天 vs 前7天
    weekly_growth = 0.0
    if len(dates) >= 14:
        recent_7 = sum(daily_data[product_id][d] for d in dates[-7:])
        prev_7 = sum(daily_data[product_id][d] for d in dates[-14:-7])
        if prev_7 > 0:
            weekly_growth = round((recent_7 - prev_7) / prev_7 * 100, 2)
    return daily_growth, weekly_growth


def compute_analysis(products, reviews, monthly_sales):
    """计算所有商品的分析指标"""
    # 按商品聚合日销量
    daily_data = compute_daily_sales(monthly_sales)

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
        product_daily = daily_data.get(pid, {})
        total_sales = sum(product_daily.values())

        # 日增长率 + 周增长率
        daily_growth, weekly_growth = compute_growth_rate(daily_data, pid)

        # 近30天每日销量趋势
        dates_sorted = sorted(product_daily.keys())
        sales_trend = [product_daily.get(d, 0) for d in dates_sorted[-30:]]

        # 关键词（从该商品的评价中提取）
        product_texts = [r['content'] for r in product_reviews]
        top_tags = extract_keywords(product_texts if product_texts else all_texts[:100])

        results.append({
            'product_id': pid,
            'category': category,
            'total_sales': total_sales,
            'daily_growth': daily_growth,
            'weekly_growth': weekly_growth,
            'review_count': review_count,
            'avg_rating': avg_rating,
            'positive_rate': positive_rate,
            'negative_rate': negative_rate,
            'top_tags': top_tags,
            'sales_trend': sales_trend,
        })

    # 按品类归一化计算爆款指数
    category_stats = {}
    for r in results:
        cat = r['category']
        if cat not in category_stats:
            category_stats[cat] = {'total_sales': 0, 'total_reviews': 0, 'growth_min': float('inf'), 'growth_max': float('-inf')}
        category_stats[cat]['total_sales'] += r['total_sales']
        category_stats[cat]['total_reviews'] += r['review_count']
        category_stats[cat]['growth_min'] = min(category_stats[cat]['growth_min'], r['weekly_growth'])
        category_stats[cat]['growth_max'] = max(category_stats[cat]['growth_max'], r['weekly_growth'])

    for r in results:
        cat = r['category']
        cs = category_stats.get(cat, {'total_sales': 1, 'total_reviews': 1, 'growth_min': 0, 'growth_max': 1})

        # 销量分：品类内市场份额
        sales_score = r['total_sales'] / cs['total_sales'] if cs['total_sales'] > 0 else 0

        # 增长分：品类内min-max归一化
        g_range = cs['growth_max'] - cs['growth_min']
        growth_score = (r['weekly_growth'] - cs['growth_min']) / g_range if g_range > 0 else 0.5

        # 评分分：1-5分映射到0-1
        rating_score = max(0, (r['avg_rating'] - 1) / 4) if r['avg_rating'] > 0 else 0.5

        # 评价分：品类内评价份额
        review_score = r['review_count'] / cs['total_reviews'] if cs['total_reviews'] > 0 else 0

        # 归一化爆款指数（0-1），各维度得分也保留供前端展示
        r['hot_score'] = round(
            0.4 * sales_score + 0.3 * growth_score + 0.2 * rating_score + 0.1 * review_score, 4
        )
        r['score_breakdown'] = {
            'sales': round(sales_score, 4),
            'growth': round(growth_score, 4),
            'rating': round(rating_score, 4),
            'review': round(review_score, 4),
        }

    return results


def write_to_hbase(results):
    """将分析结果写入HBase"""
    try:
        import happybase
        from backend.app.config import settings
        print(f"\n[HBase] 连接 HBase ({settings.hbase_host}:{settings.hbase_port})...")
        conn = happybase.Connection(settings.hbase_host, port=settings.hbase_port)

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
                row_data = {
                    'metrics:hotScore': str(r['hot_score']).encode(),
                    'metrics:positiveRate': str(r['positive_rate']).encode(),
                    'metrics:negativeRate': str(r['negative_rate']).encode(),
                    'metrics:reviewCount': str(r['review_count']).encode(),
                    'metrics:avgRating': str(r['avg_rating']).encode(),
                    'metrics:dailyGrowth': str(r['daily_growth']).encode(),
                    'metrics:weeklyGrowth': str(r['weekly_growth']).encode(),
                    'metrics:totalSales': str(r['total_sales']).encode(),
                    'metrics:topTags': json.dumps(r['top_tags'], ensure_ascii=False).encode(),
                    'trend:salesTrend': json.dumps(r['sales_trend']).encode(),
                }
                breakdown = r.get('score_breakdown', {})
                if breakdown:
                    row_data['metrics:scoreSales'] = str(breakdown.get('sales', 0)).encode()
                    row_data['metrics:scoreGrowth'] = str(breakdown.get('growth', 0)).encode()
                    row_data['metrics:scoreRating'] = str(breakdown.get('rating', 0)).encode()
                    row_data['metrics:scoreReview'] = str(breakdown.get('review', 0)).encode()
                batch.put(r['product_id'].encode(), row_data)

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
        print(f"      品类: {r['category']} | 爆款指数: {r['hot_score']:.2f} | 评分: {r['avg_rating']}")
        print(f"      总销量: {r['total_sales']} | 好评率: {r['positive_rate']*100:.1f}% | 日增长: {r['daily_growth']:.1f}% | 周增长: {r['weekly_growth']:.1f}%")
        print(f"      关键词: {', '.join(r['top_tags'][:5])}")

    # 5. 保存结果到JSON（备用）
    output_path = os.path.join(MOCK_DIR, 'product_analysis.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[完成] 分析结果已保存到: {output_path}")


if __name__ == "__main__":
    main()
