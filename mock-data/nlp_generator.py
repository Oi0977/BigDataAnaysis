"""
NLP批量生成引擎
从模板库出发，通过占位符替换+同义词替换+句式重组，批量生成评价文本。
完全离线运行，不依赖LLM API。

使用方式:
    cd 项目根目录
    uv run python mock-data/nlp_generator.py
"""

import json
import os
import random
import sys
from pathlib import Path
from typing import Optional

# 将项目根目录加入 sys.path（兼容所有运行方式）
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False
    print("警告: jieba未安装，将使用简单分词方式")
    print("安装命令: uv add jieba")

# ===========================================
# 电商领域自定义词典（用于jieba分词）
# ===========================================
DOMAIN_WORDS = [
    '质量差', '做工粗糙', '物流慢', '客服态度', '性价比', '色差',
    '续航', '卡顿', '噪音', '包装', '售后', '退货', '好评', '差评',
    '好用', '顺手', '给力', '顺滑', '精致', '划算', '超值',
    '耐用', '失望', '惊喜', '推荐', '踩雷', '翻车', '种草', '安利'
]
if JIEBA_AVAILABLE:
    for w in DOMAIN_WORDS:
        jieba.add_word(w)


# ===========================================
# 同义词词典
# ===========================================
SYNONYM_DICT = {
    "好用": ["好用", "顺手", "给力", "不错", "没毛病", "真香"],
    "质量好": ["质量好", "做工精良", "品质不错", "用料扎实"],
    "质量差": ["质量差", "做工粗糙", "偷工减料", "品质堪忧"],
    "便宜": ["便宜", "实惠", "性价比高", "划算", "超值"],
    "贵": ["贵", "价格偏高", "不太值", "有点坑"],
    "快": ["快", "迅速", "给力", "神速"],
    "慢": ["慢", "太慢了", "等了好久", "蜗牛速度"],
    "好看": ["好看", "漂亮", "颜值高", "精美", "颜值在线"],
    "难看": ["难看", "丑", "颜值低", "设计感差"],
    "推荐": ["推荐", "安利", "种草", "必入"],
    "失望": ["失望", "不满意", "踩雷", "翻车"],
    "满意": ["满意", "惊喜", "超出预期", "很满意"],
    "差": ["差", "拉胯", "不咋地", "一般般"],
    "喜欢": ["喜欢", "爱了", "太爱了", "超喜欢"],
    "舒服": ["舒服", "舒适", "很舒服", "穿着舒服"],
}


# ===========================================
# 品类特征词库
# ===========================================
CATEGORY_FEATURES = {
    "手机": ["拍照", "性能", "续航", "屏幕", "信号", "散热", "快充"],
    "电脑": ["性能", "屏幕", "散热", "键盘", "续航", "接口"],
    "服装": ["面料", "版型", "做工", "舒适度", "百搭", "显瘦"],
    "美妆": ["持妆", "显色", "滋润", "遮瑕", "轻薄", "不脱妆"],
    "食品": ["口感", "新鲜度", "分量", "包装", "味道"],
    "家居": ["质感", "设计", "实用性", "尺寸", "材质"],
    "数码": ["音质", "续航", "连接稳定性", "做工", "便携性"],
    "运动": ["舒适度", "透气性", "耐磨", "减震", "包裹性"],
}


# ===========================================
# 默认模板（当模板文件不存在时使用）
# ===========================================
DEFAULT_PRODUCT_TEMPLATES = {
    "手机": [
        "{brand}这款手机{feature}真的很不错",
        "用了{brand}手机，{feature}让我很满意",
        "{brand}手机的{feature}表现很出色",
        "入手{brand}手机，{feature}体验很棒",
    ],
    "电脑": [
        "{brand}这款电脑{feature}很不错",
        "{brand}笔记本电脑{feature}让我很满意",
        "新买的{brand}电脑，{feature}表现很好",
    ],
    "服装": [
        "{brand}这款衣服{feature}很好",
        "买了{brand}的衣服，{feature}很满意",
        "{brand}服装的{feature}真的不错",
    ],
    "美妆": [
        "{brand}这款产品{feature}很好",
        "用了{brand}，{feature}让我很惊喜",
        "{brand}的{feature}真的很棒",
    ],
    "食品": [
        "{brand}这个{feature}真的很棒",
        "买了{brand}的食品，{feature}很好",
        "{brand}食品的{feature}让我很满意",
    ],
    "家居": [
        "{brand}这款产品{feature}不错",
        "买了{brand}的家居用品，{feature}很满意",
        "{brand}家居的{feature}真的很棒",
    ],
    "数码": [
        "{brand}这款数码产品{feature}很好",
        "{brand}的{feature}表现很出色",
        "入手{brand}，{feature}体验不错",
    ],
    "运动": [
        "{brand}这款运动装备{feature}很好",
        "穿了{brand}的运动鞋，{feature}很满意",
        "{brand}运动装备的{feature}真的很棒",
    ],
}

DEFAULT_POSITIVE_TEMPLATES = {
    "手机": [
        "非常好用，{feature}表现超出预期，{brand}值得信赖！",
        "用了两个月了，{feature}一直很稳定，真心推荐！",
        "{feature}很棒，{price_desc}能买到这样的手机太值了",
        "全家人都在用{brand}，{feature}确实不错",
    ],
    "电脑": [
        "办公用完全够了，{feature}很给力",
        "用了半年，{feature}依然很稳定，满意！",
        "{feature}表现出色，{price_desc}能买到很划算",
    ],
    "服装": [
        "上身效果很好，{feature}都很满意",
        "朋友都夸好看，{feature}很不错",
        "{feature}都很好，已经回购了",
    ],
    "美妆": [
        "用了{brand}，{feature}效果真的很棒",
        "强烈推荐！{feature}都让我很满意",
        "已经是第N次回购了，{feature}真的好",
    ],
    "食品": [
        "味道很好，{feature}都很满意",
        "家人也都说好吃，{feature}不错",
        "{feature}都很好，会回购的",
    ],
    "家居": [
        "收到了，{feature}都很满意",
        "很有质感，{feature}都很好",
        "{brand}的产品{feature}确实不错",
    ],
    "数码": [
        "音质很棒，{feature}都很满意",
        "用了{brand}，{feature}真的很好",
        "{feature}表现很出色，推荐购买",
    ],
    "运动": [
        "穿起来很舒服，{feature}都很满意",
        "{feature}都很棒，运动时很给力",
        "{brand}的运动装备{feature}确实好",
    ],
}

DEFAULT_NEUTRAL_TEMPLATES = {
    "手机": [
        "一般般吧，{feature}中规中矩",
        "还行，{feature}过得去，没什么特别的",
        "{feature}一般，不过价格摆在那里",
        "用了一周，{feature}还凑合",
    ],
    "电脑": [
        "总体还可以，{feature}中规中矩",
        "日常办公够用，{feature}一般般",
        "没什么大问题，{feature}过得去",
    ],
    "服装": [
        "还行吧，{feature}一般般",
        "衣服还可以，{feature}中规中矩",
        "穿着还行，{feature}过得去",
    ],
    "美妆": [
        "效果一般，{feature}中规中矩",
        "还行吧，{feature}过得去",
        "没有太大惊喜，{feature}一般般",
    ],
    "食品": [
        "味道还行，{feature}一般般",
        "中规中矩，{feature}过得去",
        "还可以，没什么特别的",
    ],
    "家居": [
        "一般般，{feature}中规中矩",
        "还行，{feature}过得去",
        "没什么大问题，也没什么惊喜",
    ],
    "数码": [
        "音质还行，{feature}中规中矩",
        "还可以，{feature}过得去",
        "一般般，没什么特别的",
    ],
    "运动": [
        "穿着还行，{feature}中规中矩",
        "还可以，{feature}过得去",
        "一般般，没什么大问题",
    ],
}

DEFAULT_NEGATIVE_TEMPLATES = {
    "手机": [
        "不太满意，{feature}有点差",
        "用了一个月就后悔了，{feature}不行",
        "性价比太低了，{feature}让人失望",
        "{brand}的{feature}真的不行，准备退货",
    ],
    "电脑": [
        "{feature}不太行，有点失望",
        "用了几天就出问题了，{feature}很差",
        "价格不便宜但{feature}不行",
    ],
    "服装": [
        "质量太差了，{feature}都不行",
        "收到货后很失望，{feature}很差",
        "和图片差距太大了，不推荐",
    ],
    "美妆": [
        "效果不好，{feature}都很差",
        "踩雷了，{feature}都不行",
        "用了一次就闲置了，很失望",
    ],
    "食品": [
        "味道不行，{feature}都很差",
        "很失望，{feature}都不满意",
        "不会再买了，质量太差了",
    ],
    "家居": [
        "质量太差了，{feature}都不行",
        "和描述不符，很失望",
        "{feature}很差，准备退货",
    ],
    "数码": [
        "质量太差了，{feature}不行",
        "用了一周就出问题了，很失望",
        "音质很差，不推荐购买",
    ],
    "运动": [
        "穿着不舒服，{feature}都很差",
        "质量太差了，穿了一次就坏了",
        "和描述不符，很失望",
    ],
}


def extract_keywords(content: str) -> list:
    """
    从评价内容中提取关键词
    优先使用jieba分词，不可用时使用简单分词方式

    Args:
        content: 评价文本

    Returns:
        关键词列表（最多5个）
    """
    # 常见停用词
    STOP_WORDS = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一',
                  '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有',
                  '看', '好', '自己', '这', '他', '她', '它', '们', '那', '被', '从', '把',
                  '吗', '啊', '呢', '吧', '哦', '哈', '呀'}

    if JIEBA_AVAILABLE:
        # 使用jieba分词
        words = jieba.lcut(content)
    else:
        # 简单分词：按标点和空格分割，然后尝试2-4字组合
        import re
        # 先按标点分割
        segments = re.split(r'[，。！？、；：""''（）\s]+', content)
        words = []
        for seg in segments:
            if len(seg) <= 4:
                words.append(seg)
            else:
                # 尝试2-4字滑动窗口
                for i in range(len(seg)):
                    for wlen in [4, 3, 2]:
                        if i + wlen <= len(seg):
                            word = seg[i:i+wlen]
                            words.append(word)

    # 过滤: 长度>1 且 是有意义的词
    keywords = []
    seen = set()  # 去重
    for w in words:
        w = w.strip()
        if len(w) > 1 and not w.isspace() and w not in STOP_WORDS and w not in seen:
            seen.add(w)
            keywords.append(w)

    return keywords[:5]  # 最多返回5个关键词


class NLPGenerator:
    """
    NLP批量生成引擎
    从模板库出发，通过占位符替换+同义词替换+句式重组，批量生成评价文本。
    """

    def __init__(self, templates_dir: str = None):
        """
        初始化NLP生成器，加载模板库

        Args:
            templates_dir: 模板库目录路径，默认为 mock-data/templates/
        """
        if templates_dir is None:
            # 默认路径：相对于当前文件的同级templates目录
            templates_dir = str(Path(__file__).parent / "templates")

        self.templates_dir = templates_dir
        self.templates = {
            "product": {},
            "positive": {},
            "neutral": {},
            "negative": {}
        }

        # 加载模板库
        self._load_templates()

    def _load_templates(self):
        """加载所有模板文件"""
        template_files = {
            "product": "product_templates.json",
            "positive": "positive_templates.json",
            "neutral": "neutral_templates.json",
            "negative": "negative_templates.json"
        }

        for template_type, filename in template_files.items():
            filepath = os.path.join(self.templates_dir, filename)

            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        self.templates[template_type] = json.load(f)
                    print(f"✓ 已加载模板: {filename}")
                except Exception as e:
                    print(f"⚠ 加载模板失败 {filename}: {e}")
                    self.templates[template_type] = {}
            else:
                print(f"⚠ 模板文件不存在: {filepath}")
                print(f"  将使用内置默认模板")

        # 如果某个品类在文件中没有模板，使用默认模板
        self._apply_defaults()

    def _apply_defaults(self):
        """为没有模板的品类应用默认模板"""
        # 产品描述默认模板
        for category in DEFAULT_PRODUCT_TEMPLATES:
            if category not in self.templates["product"]:
                self.templates["product"][category] = DEFAULT_PRODUCT_TEMPLATES[category]

        # 好评默认模板
        for category in DEFAULT_POSITIVE_TEMPLATES:
            if category not in self.templates["positive"]:
                self.templates["positive"][category] = DEFAULT_POSITIVE_TEMPLATES[category]

        # 中评默认模板
        for category in DEFAULT_NEUTRAL_TEMPLATES:
            if category not in self.templates["neutral"]:
                self.templates["neutral"][category] = DEFAULT_NEUTRAL_TEMPLATES[category]

        # 差评默认模板
        for category in DEFAULT_NEGATIVE_TEMPLATES:
            if category not in self.templates["negative"]:
                self.templates["negative"][category] = DEFAULT_NEGATIVE_TEMPLATES[category]

    def _get_price_description(self, price: float) -> str:
        """
        根据价格区间返回价格描述

        Args:
            price: 商品价格

        Returns:
            价格描述字符串
        """
        if price < 100:
            return "百元以内"
        elif price < 500:
            return "平价好物"
        elif price < 2000:
            return "千元档"
        elif price < 5000:
            return "高端旗舰"
        else:
            return "顶级奢华"

    def _get_feature(self, category: str) -> str:
        """
        根据品类获取随机特征词

        Args:
            category: 商品品类

        Returns:
            特征词
        """
        features = CATEGORY_FEATURES.get(category, ["质量", "外观", "手感"])
        return random.choice(features)

    def _replace_placeholders(self, template: str, product_info: dict = None) -> str:
        """
        替换模板中的占位符

        Args:
            template: 包含占位符的模板字符串
            product_info: 商品信息字典，包含brand/price等

        Returns:
            替换后的字符串
        """
        result = template

        # 默认品牌选项
        default_brands = ["华为", "小米", "苹果", "三星", "OPPO", "vivo", "联想", "戴尔",
                         "Nike", "Adidas", "优衣库", "ZARA", "欧莱雅", "兰蔻", "三只松鼠",
                         "良品铺子", "美的", "格力", "索尼", "JBL"]

        # 获取品牌
        brand = "华为"
        price = 199.0
        if product_info:
            brand = product_info.get("brand", random.choice(default_brands))
            price = float(product_info.get("price", 199.0))
        else:
            brand = random.choice(default_brands)

        # 获取品类
        category = product_info.get("category", "手机") if product_info else "手机"

        # 替换占位符
        result = result.replace("{brand}", brand)
        result = result.replace("{price_desc}", self._get_price_description(price))
        result = result.replace("{feature}", self._get_feature(category))

        return result

    def _apply_synonym_replacement(self, text: str, probability: float = 0.3) -> str:
        """
        对文本进行同义词替换

        Args:
            text: 原始文本
            probability: 每个词触发替换的概率，默认30%

        Returns:
            替换后的文本
        """
        result = text

        for original_word, synonyms in SYNONYM_DICT.items():
            if original_word in result:
                # 按概率决定是否替换
                if random.random() < probability:
                    replacement = random.choice(synonyms)
                    # 避免替换成自己
                    if replacement != original_word:
                        result = result.replace(original_word, replacement, 1)

        return result

    def _get_rating(self, sentiment: str) -> int:
        """
        根据情感类型自动分配评分

        Args:
            sentiment: 情感类型 positive/neutral/negative

        Returns:
            评分 (1-5)
        """
        if sentiment == "positive":
            return random.choice([4, 4, 4, 5, 5])
        elif sentiment == "neutral":
            return 3
        elif sentiment == "negative":
            return random.choice([1, 1, 2])
        else:
            return 3  # 默认中评

    def generate_review(self, category: str, sentiment: str, product_info: dict = None) -> dict:
        """
        生成一条评价

        Args:
            category: 商品品类（手机/电脑/服装/美妆/食品/家居/数码/运动）
            sentiment: 情感类型 (positive/neutral/negative)
            product_info: 可选，商品信息字典，包含brand/price等

        Returns:
            dict: {"content": "...", "rating": int, "sentiment": str, "keywords": list}
        """
        # 获取对应类型和品类的模板
        template_list = self.templates.get(sentiment, {}).get(category, [])

        if not template_list:
            # 如果没有模板，使用好评的通用模板
            template_list = ["这是一条关于{category}的评价，{feature}还不错"]
            # 替换category占位符
            template_list = [t.replace("{category}", category) for t in template_list]

        # 随机选择模板
        template = random.choice(template_list)

        # 占位符替换
        content = self._replace_placeholders(template, product_info)

        # 同义词替换（30%概率）
        content = self._apply_synonym_replacement(content, probability=0.3)

        # 提取关键词
        keywords = extract_keywords(content)

        # 自动分配评分
        rating = self._get_rating(sentiment)

        return {
            "content": content,
            "rating": rating,
            "sentiment": sentiment,
            "keywords": keywords
        }

    def generate_reviews_for_product(self, product: dict, count: int = 10) -> list:
        """
        为一个商品生成多条评价

        按比例: 好评60%, 中评20%, 差评20%

        Args:
            product: 商品信息字典，应包含category/brand/price等字段
            count: 生成评价数量，默认10条

        Returns:
            list: 评价列表
        """
        reviews = []

        # 计算各类型评价数量
        positive_count = int(count * 0.6)
        neutral_count = int(count * 0.2)
        negative_count = count - positive_count - neutral_count

        # 生成好评
        for _ in range(positive_count):
            review = self.generate_review(
                category=product.get("category", "手机"),
                sentiment="positive",
                product_info=product
            )
            reviews.append(review)

        # 生成中评
        for _ in range(neutral_count):
            review = self.generate_review(
                category=product.get("category", "手机"),
                sentiment="neutral",
                product_info=product
            )
            reviews.append(review)

        # 生成差评
        for _ in range(negative_count):
            review = self.generate_review(
                category=product.get("category", "手机"),
                sentiment="negative",
                product_info=product
            )
            reviews.append(review)

        # 随机打乱顺序
        random.shuffle(reviews)

        return reviews

    def generate_product_description(self, category: str, brand: str, price: float) -> str:
        """
        生成商品描述

        Args:
            category: 商品品类
            brand: 品牌名称
            price: 商品价格

        Returns:
            商品描述字符串
        """
        # 获取产品描述模板
        template_list = self.templates.get("product", {}).get(category, [])

        if not template_list:
            # 使用默认模板
            template_list = DEFAULT_PRODUCT_TEMPLATES.get(category, [
                "{brand}品牌的{category}产品，品质值得信赖"
            ])

        # 随机选择模板
        template = random.choice(template_list)

        # 替换占位符
        description = template.replace("{brand}", brand)
        description = description.replace("{price_desc}", self._get_price_description(price))
        description = description.replace("{feature}", self._get_feature(category))
        description = description.replace("{category}", category)

        # 同义词替换
        description = self._apply_synonym_replacement(description, probability=0.2)

        return description

    def batch_generate_reviews(self, products: list, reviews_per_product: int = 10) -> list:
        """
        批量为所有商品生成评价

        Args:
            products: 商品列表
            reviews_per_product: 每个商品生成的评价数量，默认10条

        Returns:
            list: 所有评价的列表
        """
        all_reviews = []

        for product in products:
            product_reviews = self.generate_reviews_for_product(product, reviews_per_product)

            # 为每条评价添加商品ID
            for review in product_reviews:
                review["product_id"] = product.get("id", "")
                review["product_name"] = product.get("name", "")

            all_reviews.extend(product_reviews)

        return all_reviews


# ===========================================
# 命令行测试入口
# ===========================================
if __name__ == "__main__":
    # 创建生成器实例
    generator = NLPGenerator()

    # 测试商品信息
    test_product = {
        "id": "TEST001",
        "name": "测试手机",
        "category": "手机",
        "brand": "华为",
        "price": 4999.0
    }

    print("=" * 60)
    print("NLP批量生成引擎 - 测试")
    print("=" * 60)

    # 测试生成单条评价
    print("\n【测试1：生成单条评价】")
    review = generator.generate_review("手机", "positive", test_product)
    print(f"内容: {review['content']}")
    print(f"评分: {review['rating']}")
    print(f"情感: {review['sentiment']}")
    print(f"关键词: {review['keywords']}")

    # 测试为商品生成多条评价
    print("\n【测试2：为商品生成10条评价】")
    reviews = generator.generate_reviews_for_product(test_product, 10)
    for i, r in enumerate(reviews, 1):
        print(f"{i}. [{r['rating']}星] {r['content']}")

    # 测试生成商品描述
    print("\n【测试3：生成商品描述】")
    desc = generator.generate_product_description("手机", "华为", 4999.0)
    print(f"描述: {desc}")

    # 统计评分分布
    print("\n【统计：评分分布】")
    rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in reviews:
        rating_counts[r['rating']] = rating_counts.get(r['rating'], 0) + 1
    for rating, count in sorted(rating_counts.items()):
        print(f"{rating}星: {count}条")

    print("\n" + "=" * 60)
    print("测试完成！")
