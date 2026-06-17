"""
评价分析计算脚本（纯Python版）
使用 jieba TextRank + LDA + K-Means + SnowNLP

运行方式:
    cd 项目根目录/backend
    uv run python ../scripts/compute_review_analysis.py
"""
import os
import sys
import json
from collections import Counter, defaultdict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOCK_DIR = os.path.join(PROJECT_ROOT, "mock-data")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 停用词 & 领域词典（与 nlp_service.py 一致）
STOP_WORDS = {
    '的', '了', '是', '在', '我', '有', '和', '就', '不', '人',
    '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
    '你', '会', '着', '没有', '看', '好', '自己', '这', '他', '她',
    '它', '们', '那', '被', '从', '把', '还', '没', '过', '来',
    '对', '为', '以', '与', '或', '但', '而', '又', '能', '可',
    '已经', '这个', '那个', '什么', '怎么', '如果', '因为', '所以',
    '虽然', '但是', '然后', '其实', '真的', '比较', '非常', '太',
    '用', '时', '天', '年', '月', '日', '时候', '东西', '地方',
    '问题', '感觉', '觉得', '应该', '可能', '需要', '知道', '时候',
}

DOMAIN_WORDS = [
    '质量差', '做工粗糙', '物流慢', '客服态度', '性价比', '色差',
    '续航', '卡顿', '噪音', '包装', '售后', '退货',
    '甲醛', '线头', '偏小', '偏大', '压坏', '不清晰',
    '质量', '做工', '材质', '耐用', '客服', '售后',
    '态度', '回复', '物流', '快递', '配送', '时效',
    '图片', '实物', '颜色', '尺寸', '价格', '性价比',
    '功能', '性能', '卡顿', '续航', '气味', '安装',
]


# 单字停用词
SINGLE_STOP = set('的了是在我有和就不人都一上也很到说要去你会着没看好自己这他她它们那被从把还没过来对为以与或但而又能可吗吧呢哦哈呀嘛啦')


def load_json(filename):
    path = os.path.join(MOCK_DIR, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def tokenize_reviews(reviews):
    """jieba分词 + 过滤"""
    try:
        import jieba
    except ImportError:
        print("[错误] jieba 未安装")
        return [], []

    for word in DOMAIN_WORDS:
        jieba.add_word(word)

    tokenized_texts = []
    all_words_list = []
    for review in reviews:
        content = review.get('content', '')
        if not content:
            tokenized_texts.append('')
            all_words_list.append([])
            continue
        words = jieba.lcut(content)
        filtered = [w for w in words if len(w) > 1 and w not in STOP_WORDS]
        tokenized_texts.append(' '.join(filtered))
        all_words_list.append(filtered)
    return tokenized_texts, all_words_list


def extract_keywords_textrank(reviews, top_n=20):
    """SnowNLP筛出差评 → jieba分词 → 词频统计提取投诉关键词"""
    try:
        import jieba
        from snownlp import SnowNLP
    except ImportError:
        print("[错误] jieba 或 snownlp 未安装")
        return []

    # 品牌/品类停用词
    BRAND_STOP = {
        '华为', '小米', '苹果', '三星', 'OPPO', 'vivo', '荣耀', '联想', '戴尔',
        '华硕', '索尼', 'BOSE', '漫步者', 'Nike', 'Adidas', '优衣库', 'ZARA',
        '太平鸟', '森马', 'UR', '完美日记', '花西子', '兰蔻', '雅诗兰黛', 'MAC',
        '三只松鼠', '良品铺子', '百草味', '来伊份', '宜家', '无印良品', '网易严选',
        '名创优品', 'JBL', 'Mate', 'Pro', 'Ultra', 'AirPods', 'iPhone', 'MacBook',
        '网易', '严选', '伊份', '运动', '耳机', '手机', '电脑', '食品', '家居',
        '数码', '服装', '美妆', '产品', '品牌',
    }

    # 筛选差评
    negative_texts = []
    for r in reviews:
        content = r.get('content', '')
        if not content:
            continue
        try:
            if SnowNLP(content).sentiments < 0.3:
                negative_texts.append(content)
        except Exception:
            pass

    print(f"  差评筛选: {len(negative_texts)}/{len(reviews)} 条")

    if not negative_texts:
        negative_texts = [r.get('content', '') for r in reviews if r.get('content')]

    # jieba分词 → 词频统计
    word_count = Counter()
    for text in negative_texts:
        words = jieba.lcut(text)
        for w in words:
            if len(w) > 1 and w not in BRAND_STOP and w not in SINGLE_STOP:
                word_count[w] += 1

    # 按词频排序，取top_n（返回实际出现次数）
    keywords = [
        {'word': w, 'count': count}
        for w, count in word_count.most_common(top_n)
    ]
    return keywords


def compute_count_vectorizer(tokenized_texts):
    """构建词袋矩阵（用于LDA和K-Means）"""
    try:
        from sklearn.feature_extraction.text import CountVectorizer
    except ImportError:
        print("[错误] scikit-learn 未安装")
        return None, None

    non_empty = [t for t in tokenized_texts if t.strip()]
    if len(non_empty) < 2:
        print("[警告] 有效评价不足（<2条），跳过")
        return None, None

    vectorizer = CountVectorizer(max_features=3000, min_df=2)
    count_matrix = vectorizer.fit_transform(tokenized_texts)
    feature_names = vectorizer.get_feature_names_out()
    print(f"  词袋矩阵: {count_matrix.shape[0]} 条评价 x {count_matrix.shape[1]} 个特征")
    return count_matrix, feature_names


def compute_lda(count_matrix, n_components=5):
    """LDA主题建模"""
    try:
        from sklearn.decomposition import LatentDirichletAllocation
    except ImportError:
        print("[错误] scikit-learn 未安装")
        return None, None

    if count_matrix is None:
        return None, None

    lda = LatentDirichletAllocation(n_components=n_components, max_iter=20, random_state=42)
    lda_output = lda.fit_transform(count_matrix)
    print(f"  LDA: {n_components} 个主题")
    return lda, lda_output


def extract_topic_keywords(lda_model, feature_names, n_top_words=10):
    """提取每个主题的Top关键词"""
    if lda_model is None:
        return []
    topics = []
    for topic in lda_model.components_:
        top_indices = topic.argsort()[::-1][:n_top_words]
        topics.append([feature_names[i] for i in top_indices])
    return topics


def compute_topic_distribution(lda_output):
    """全局主题分布"""
    if lda_output is None or len(lda_output) == 0:
        return []
    import numpy as np
    avg = np.mean(lda_output, axis=0)
    return [round(float(w), 6) for w in avg]


def compute_kmeans(count_matrix, k_range=range(2, 9)):
    """K-Means聚类（自动选K：轮廓系数最优）"""
    try:
        from sklearn.cluster import KMeans
        from sklearn.metrics import silhouette_score
    except ImportError:
        print("[错误] scikit-learn 未安装")
        return None, [], 5

    if count_matrix is None:
        return None, [], 5

    best_k = 5
    best_score = -1
    best_kmeans = None
    best_labels = None

    for k in k_range:
        if k >= count_matrix.shape[0]:
            break
        kmeans = KMeans(n_clusters=k, init='k-means++', n_init=10, random_state=42)
        labels = kmeans.fit_predict(count_matrix)
        try:
            score = silhouette_score(count_matrix, labels, sample_size=min(1000, count_matrix.shape[0]))
        except Exception:
            score = -1
        print(f"  K={k}: 轮廓系数={score:.4f}")
        if score > best_score:
            best_score = score
            best_k = k
            best_kmeans = kmeans
            best_labels = labels

    print(f"  K-Means 最优K={best_k} (轮廓系数={best_score:.4f})")
    return best_kmeans, best_labels, best_k


def extract_cluster_info(labels, count_matrix, feature_names, n_top=5):
    """每个簇的数量和代表词"""
    if labels is None or count_matrix is None:
        return {}, {}
    import numpy as np
    n_clusters = max(labels) + 1 if len(labels) > 0 else 0
    counts = {}
    keywords = {}
    dense = count_matrix.toarray()
    for c in range(n_clusters):
        mask = labels == c
        count = int(np.sum(mask))
        if count > 0:
            counts[str(c)] = count
            avg_vec = np.mean(dense[mask], axis=0)
            top_idx = avg_vec.argsort()[::-1][:n_top]
            keywords[str(c)] = [feature_names[i] for i in top_idx]
        else:
            keywords[str(c)] = []
    return counts, keywords


def analyze_sentiment_rating(reviews):
    """SnowNLP情感分析 + 评分分布"""
    try:
        from snownlp import SnowNLP
    except ImportError:
        print("[错误] snownlp 未安装")
        return {}, {}

    sentiment_count = Counter()
    rating_count = Counter()
    for r in reviews:
        rating_count[str(r.get('rating', 0))] += 1
        content = r.get('content', '')
        if content:
            try:
                score = SnowNLP(content).sentiments
                if score < 0.3:
                    sentiment_count['negative'] += 1
                elif score < 0.7:
                    sentiment_count['neutral'] += 1
                else:
                    sentiment_count['positive'] += 1
            except Exception:
                sentiment_count['neutral'] += 1
        else:
            sentiment_count['neutral'] += 1
    return dict(sentiment_count), dict(rating_count)


def aggregate_by_product(reviews, all_words_list, count_matrix, feature_names,
                         lda_output, cluster_labels, global_topic_kw, product_results):
    """按product_id聚合"""
    product_indices = defaultdict(list)
    for i, r in enumerate(reviews):
        product_indices[r['product_id']].append(i)

    # 品牌/品类/通用停用词
    BRAND_STOP = {
        '华为', '小米', '苹果', '三星', 'OPPO', 'vivo', '荣耀', '联想', '戴尔',
        '华硕', '索尼', 'BOSE', '漫步者', 'Nike', 'Adidas', '优衣库', 'ZARA',
        '太平鸟', '森马', 'UR', '完美日记', '花西子', '兰蔻', '雅诗兰黛', 'MAC',
        '三只松鼠', '良品铺子', '百草味', '来伊份', '伊份', '宜家', '无印良品', '网易严选', '网易', '严选',
        '名创优品', 'JBL', 'Mate', 'Pro', 'Ultra', 'AirPods', 'iPhone', 'MacBook',
        '运动', '耳机', '装备', '穿着', '一次', '手机', '电脑', '食品', '家居',
        '数码', '服装', '美妆', '产品', '品牌', '款式', '颜色', '尺码',
        '真的', '非常', '特别', '比较', '其实', '已经', '居然', '还是', '而且',
        '但是', '不是', '没有', '这个', '那个', '什么', '怎么', '一个', '就是',
        '确实', '不过', '如果', '因为', '所以', '虽然', '然后', '可以', '可能',
        '舒服', '很棒', '不错', '满意', '推荐', '喜欢', '好评', '好用', '划算',
    }

    for pid, indices in product_indices.items():
        # 该产品的差评关键词（词频统计）
        try:
            import jieba
            from snownlp import SnowNLP
            word_count = Counter()
            for i in indices:
                content = reviews[i].get('content', '')
                if not content:
                    continue
                try:
                    is_negative = SnowNLP(content).sentiments < 0.3
                except Exception:
                    is_negative = False
                words = jieba.lcut(content)
                for w in words:
                    if len(w) > 1 and w not in BRAND_STOP and w not in SINGLE_STOP:
                        word_count[w] += 3 if is_negative else 1
            total = sum(word_count.values()) or 1
            product_kw = [
                {'word': w, 'score': round(c / total, 6)}
                for w, c in word_count.most_common(10)
            ]
        except Exception:
            product_kw = []

        # 主题分布
        if lda_output is not None and len(indices) > 0:
            import numpy as np
            pd = [round(float(w), 6) for w in np.mean(lda_output[indices], axis=0)]
        else:
            pd = [0.0] * 5

        # 聚类分布（只保留有评价的簇）
        if cluster_labels is not None and count_matrix is not None and len(indices) > 0:
            import numpy as np
            pc = cluster_labels[indices]
            cc = {}
            ck = {}
            dense = count_matrix[indices].toarray()
            n_c = max(cluster_labels) + 1
            for c in range(n_c):
                mask = pc == c
                count = int(np.sum(mask))
                if count > 0:
                    cc[str(c)] = count
                    avg_v = np.mean(dense[mask], axis=0)
                    top_i = avg_v.argsort()[::-1][:5]
                    ck[str(c)] = [feature_names[i] for i in top_i]
        else:
            cc = {}
            ck = {}

        # 情感+评分
        product_reviews = [reviews[i] for i in indices]
        sent, rat = analyze_sentiment_rating(product_reviews)

        product_results[pid] = {
            'product_id': pid,
            'review_count': len(indices),
            'keywords': product_kw,
            'topic_distribution': pd,
            'topic_keywords': global_topic_kw,
            'cluster_labels': cc,
            'cluster_keywords': ck,
            'sentiment_distribution': sent,
            'rating_distribution': rat,
        }


def write_to_hbase(product_results):
    """写入HBase"""
    try:
        import happybase
        from backend.app.config import settings
        print(f"\n[HBase] 连接 HBase ({settings.hbase_host}:{settings.hbase_port})...")
        conn = happybase.Connection(settings.hbase_host, port=settings.hbase_port)
        existing = conn.tables()
        if b'review_analysis' not in existing:
            conn.create_table('review_analysis', {'stats': dict(max_versions=1)})
            print("[HBase] 创建表: review_analysis")
        table = conn.table('review_analysis')
        results_list = [v for k, v in product_results.items() if not k.startswith('_')]
        print(f"[HBase] 写入 {len(results_list)} 条...")
        with table.batch() as batch:
            for r in results_list:
                row = {
                    'stats:highFreqKeywords': json.dumps(r['keywords'], ensure_ascii=False).encode(),
                    'stats:sentimentDistribution': json.dumps(r['sentiment_distribution'], ensure_ascii=False).encode(),
                    'stats:ratingDistribution': json.dumps(r['rating_distribution'], ensure_ascii=False).encode(),
                    'stats:topicDistribution': json.dumps(r['topic_distribution'], ensure_ascii=False).encode(),
                    'stats:topicKeywords': json.dumps(r['topic_keywords'], ensure_ascii=False).encode(),
                    'stats:clusterLabels': json.dumps(r['cluster_labels'], ensure_ascii=False).encode(),
                    'stats:clusterKeywords': json.dumps(r['cluster_keywords'], ensure_ascii=False).encode(),
                    'stats:updateTime': __import__('datetime').datetime.now().isoformat().encode(),
                }
                batch.put(r['product_id'].encode(), row)
        conn.close()
        print(f"[HBase] 成功写入 {len(results_list)} 条")
    except Exception as e:
        print(f"[HBase] 写入失败: {e}")


def main():
    print("=" * 60)
    print("  评价分析计算脚本（jieba + LDA + K-Means + SnowNLP）")
    print("=" * 60)

    print("\n--- 加载评价数据 ---")
    reviews = load_json('reviews.json')
    print(f"  评价总数: {len(reviews)} 条")
    if not reviews:
        print("[警告] 没有评价数据，退出")
        return

    print("\n--- 分词预处理 ---")
    tokenized_texts, all_words_list = tokenize_reviews(reviews)
    non_empty = sum(1 for t in tokenized_texts if t.strip())
    print(f"  有效评价: {non_empty} 条")

    print("\n--- TextRank 关键词提取 ---")
    global_keywords = extract_keywords_textrank(reviews, top_n=20)
    print(f"  Top 5: {[kw['word'] for kw in global_keywords[:5]]}")

    print("\n--- 构建词袋矩阵 ---")
    count_matrix, feature_names = compute_count_vectorizer(tokenized_texts)

    print("\n--- LDA 主题建模 ---")
    lda_model, lda_output = compute_lda(count_matrix)
    topic_keywords = extract_topic_keywords(lda_model, feature_names)
    topic_dist = compute_topic_distribution(lda_output)

    print("\n--- K-Means 聚类 ---")
    kmeans_model, cluster_labels, optimal_k = compute_kmeans(count_matrix)
    global_cc, global_ck = extract_cluster_info(cluster_labels, count_matrix, feature_names)

    print("\n--- 按产品聚合 ---")
    product_results = {'_global_topic_kw': topic_keywords, '_global_keywords': global_keywords}
    aggregate_by_product(reviews, all_words_list, count_matrix, feature_names,
                         lda_output, cluster_labels, topic_keywords, product_results)
    product_count = sum(1 for k in product_results if not k.startswith('_'))
    print(f"  聚合完成: {product_count} 个产品")

    write_to_hbase(product_results)

    # 保存JSON（包含全局关键词 + 各产品数据）
    output_data = {
        'globalKeywords': global_keywords,
        'topicKeywords': topic_keywords,
        'products': [v for k, v in product_results.items() if not k.startswith('_')]
    }
    output_path = os.path.join(MOCK_DIR, 'review_analysis.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"\n[完成] 已保存到: {output_path}")

    print("\n" + "=" * 60)
    print("  评价分析摘要")
    print("=" * 60)
    print("\n--- Top 5 关键词 ---")
    for kw in global_keywords[:5]:
        print(f"  {kw['word']}: {kw.get('count', kw.get('score', 0))}")
    print("\n--- Top 5 主题 ---")
    for i, kw_list in enumerate(topic_keywords[:5]):
        print(f"  主题 {i+1}: {', '.join(kw_list[:5])}")
    print(f"\n--- 主题分布 ---")
    for i, w in enumerate(topic_dist[:5]):
        print(f"  主题 {i+1}: {w*100:.1f}%")
    print(f"\n--- 聚类分布 ---")
    total = sum(global_cc.values()) if global_cc else 0
    for c, count in sorted(global_cc.items()):
        pct = count / total * 100 if total > 0 else 0
        kws = ', '.join(global_ck.get(c, [])[:3])
        print(f"  簇 {c}: {count} 条 ({pct:.1f}%) | {kws}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
