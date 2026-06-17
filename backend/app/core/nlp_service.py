"""
NLP 服务 - 封装 jieba 分词和 SnowNLP 情感分析
"""
import jieba
from collections import Counter
from snownlp import SnowNLP

# 电商差评领域词典（提高分词准确率）
DOMAIN_WORDS = [
    '质量差', '做工粗糙', '物流慢', '客服态度', '性价比', '色差',
    '续航', '卡顿', '噪音', '包装', '售后', '退货',
    '甲醛', '线头', '偏小', '偏大', '压坏', '不清晰',
    '质量', '做工', '材质', '耐用', '客服', '售后',
    '态度', '回复', '物流', '快递', '配送', '时效',
    '图片', '实物', '颜色', '尺寸', '价格', '性价比',
    '功能', '性能', '卡顿', '续航', '气味', '安装'
]

# 加载领域词典
for word in DOMAIN_WORDS:
    jieba.add_word(word)

# 电商领域停用词（过滤无意义词）
STOP_WORDS = {
    '的', '了', '是', '在', '我', '有', '和', '就', '不', '人',
    '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
    '你', '会', '着', '没有', '看', '好', '自己', '这', '他', '她',
    '它', '们', '那', '被', '从', '把', '还', '没', '过', '来',
    '对', '为', '以', '与', '或', '但', '而', '又', '能', '可',
    '已经', '这个', '那个', '什么', '怎么', '如果', '因为', '所以',
    '虽然', '但是', '然后', '其实', '真的', '比较', '非常', '太',
    '用', '时', '天', '年', '月', '日', '时候', '东西', '地方',
    '问题', '感觉', '觉得', '应该', '可能', '需要', '知道', '时候'
}


class NLPService:
    """NLP 服务类"""

    def extract_keywords(self, text: str, top_k: int = 5) -> list:
        """
        从文本中提取关键词
        使用 jieba 分词 + 词频统计
        """
        if not text:
            return []

        words = jieba.lcut(text)
        # 过滤停用词和单字
        filtered = [w for w in words if len(w) > 1 and w not in STOP_WORDS]
        # 词频统计
        counter = Counter(filtered)
        return [w for w, _ in counter.most_common(top_k)]

    def analyze_sentiment(self, text: str) -> str:
        """
        情感分析
        使用 SnowNLP 计算情感得分
        """
        if not text:
            return "neutral"

        score = SnowNLP(text).sentiments
        if score < 0.3:
            return "negative"
        elif score < 0.7:
            return "neutral"
        else:
            return "positive"

    def batch_analyze(self, texts: list) -> list:
        """
        批量情感分析
        返回 (sentiment, score) 列表
        """
        results = []
        for text in texts:
            if not text:
                results.append(("neutral", 0.5))
                continue
            score = SnowNLP(text).sentiments
            if score < 0.3:
                sentiment = "negative"
            elif score < 0.7:
                sentiment = "neutral"
            else:
                sentiment = "positive"
            results.append((sentiment, score))
        return results


# 模块级别单例
nlp_service = NLPService()
