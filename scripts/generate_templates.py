#!/usr/bin/env python3
"""
一次性运行脚本：调用阿里云百炼LLM（qwen-plus）为8个电商品类生成文本模板库。

生成的模板文件保存在 mock-data/templates/ 目录：
- product_templates.json: 商品描述模板（每品类20条）
- positive_templates.json: 好评模板（每品类30条）
- neutral_templates.json: 中评模板（每品类20条）
- negative_templates.json: 差评模板（每品类20条）

支持断点续传：如果某个品类的模板已生成，会跳过。
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# ============================================================
# 配置区
# ============================================================

# 项目根目录（scripts/ 的上一级）
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 读取 backend/.env 中的API配置
ENV_PATH = PROJECT_ROOT / "backend" / ".env"
load_dotenv(ENV_PATH)

AI_API_KEY = os.getenv("AI_API_KEY")
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
AI_MODEL = os.getenv("AI_MODEL", "qwen-plus")

# 输出目录
OUTPUT_DIR = PROJECT_ROOT / "mock-data" / "templates"

# 品类和对应品牌
CATEGORIES = {
    "手机": ["苹果", "华为", "小米", "OPPO", "vivo", "荣耀"],
    "电脑": ["苹果", "联想", "华为", "戴尔", "华硕"],
    "服装": ["优衣库", "ZARA", "太平鸟", "UR", "森马"],
    "美妆": ["完美日记", "花西子", "兰蔻", "雅诗兰黛", "MAC"],
    "食品": ["三只松鼠", "良品铺子", "百草味", "来伊份"],
    "家居": ["宜家", "无印良品", "网易严选", "名创优品"],
    "数码": ["索尼", "BOSE", "苹果", "漫步者", "小米"],
    "运动": ["耐克", "阿迪达斯", "李宁", "安踏", "匹克"],
}

# ============================================================
# Prompt 模板
# ============================================================

SYSTEM_PROMPT = """你是一个电商文案生成专家，擅长为各种电商品类生成自然、真实的文本模板。
请严格按照要求的JSON格式输出，不要输出任何多余内容。"""


def build_user_prompt(category: str, brands: list[str]) -> str:
    """构建发送给LLM的用户提示词，一次性生成某品类的4种模板。"""
    brand_list = "、".join(brands)
    return f"""请为「{category}」品类生成以下4种文本模板，品牌包括：{brand_list}。

## 1. 商品描述模板（product）—— 共20条
- 用占位符标注可替换部分：{{brand}} {{price_desc}} {{feature}}
- {{brand}} 从品牌列表中选择
- {{price_desc}} 可选值：百元档、千元档、高端旗舰
- {{feature}} 可选值：性能、续航、拍照、外观、舒适度、做工、音质、设计感、面料、口感、收纳、便携 等
- 风格：电商文案风格，简短有吸引力

## 2. 好评模板（positive）—— 共30条
- 覆盖6个维度：质量、性价比、物流、服务、外观、功能（每个维度约5条）
- 语气：真实用户好评，口语化，适当包含品牌名
- 长度：20-60字

## 3. 中评模板（neutral）—— 共20条
- 优缺点并存的语气，先说优点再说不足
- 语气：真实用户中肯评价
- 长度：20-60字

## 4. 差评模板（negative）—— 共20条
- 覆盖常见痛点：质量问题、物流问题、售后服务、性价比低、功能不符、外观瑕疵 等
- 语气：真实用户不满，口语化
- 长度：20-60字

## 输出格式（严格JSON）

```json
{{
  "product": ["模板1", "模板2", ...],
  "positive": ["模板1", "模板2", ...],
  "neutral": ["模板1", "模板2", ...],
  "negative": ["模板1", "模板2", ...]
}}
```

请直接输出JSON，不要包含任何解释文字或markdown代码块标记。"""


# ============================================================
# 工具函数
# ============================================================


def init_client() -> OpenAI:
    """初始化OpenAI兼容客户端。"""
    if not AI_API_KEY:
        print("[错误] 未找到 AI_API_KEY，请检查 backend/.env 文件")
        sys.exit(1)
    return OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)


def load_existing_progress() -> dict[str, set[str]]:
    """加载已有的生成进度，返回每个文件已包含的品类集合。

    返回格式:
    {
        "product": {"手机", "电脑", ...},
        "positive": {"手机", ...},
        ...
    }
    """
    progress = {
        "product": set(),
        "positive": set(),
        "neutral": set(),
        "negative": set(),
    }

    file_map = {
        "product": "product_templates.json",
        "positive": "positive_templates.json",
        "neutral": "neutral_templates.json",
        "negative": "negative_templates.json",
    }

    for key, filename in file_map.items():
        filepath = OUTPUT_DIR / filename
        if filepath.exists():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                progress[key] = set(data.keys())
            except (json.JSONDecodeError, IOError):
                pass

    return progress


def save_templates(templates: dict[str, list[str]], filename: str, category: str):
    """将单个文件的模板追加保存。

    读取已有内容，合并新内容后写回。
    """
    filepath = OUTPUT_DIR / filename
    existing = {}
    if filepath.exists():
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing = {}

    existing[category] = templates

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)


def parse_llm_response(raw: str) -> dict[str, list[str]]:
    """解析LLM返回的JSON响应。

    处理可能的markdown代码块包裹情况。
    """
    text = raw.strip()

    # 去除可能的markdown代码块标记
    if text.startswith("```"):
        lines = text.split("\n")
        # 去掉首行和尾行的 ``` 标记
        if lines[-1].strip() == "```":
            lines = lines[1:-1]
        else:
            lines = lines[1:]
        text = "\n".join(lines).strip()

    data = json.loads(text)

    # 验证必要字段
    required_keys = ["product", "positive", "neutral", "negative"]
    for key in required_keys:
        if key not in data:
            raise ValueError(f"LLM返回缺少字段: {key}")

    return data


# ============================================================
# 主流程
# ============================================================


def generate_category(client: OpenAI, category: str, brands: list[str]) -> dict[str, list[str]]:
    """调用LLM为单个品类生成4种模板。"""
    prompt = build_user_prompt(category, brands)

    print(f"  -> 调用LLM生成「{category}」品类模板...")
    response = client.chat.completions.create(
        model=AI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,
        max_tokens=4096,
    )

    raw_content = response.choices[0].message.content
    if not raw_content:
        raise ValueError("LLM返回内容为空")

    templates = parse_llm_response(raw_content)

    # 打印生成数量
    for key, items in templates.items():
        print(f"    {key}: {len(items)} 条")

    return templates


def main():
    """主入口：遍历8个品类，生成模板并保存。"""
    print("=" * 60)
    print("电商文本模板生成器")
    print(f"LLM模型: {AI_MODEL}")
    print(f"API地址: {AI_BASE_URL}")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 60)

    # 确保输出目录存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 初始化LLM客户端
    client = init_client()
    print("[成功] LLM客户端初始化完成\n")

    # 加载已有进度
    progress = load_existing_progress()
    file_keys = ["product", "positive", "neutral", "negative"]
    file_names = {
        "product": "product_templates.json",
        "positive": "positive_templates.json",
        "neutral": "neutral_templates.json",
        "negative": "negative_templates.json",
    }

    success_count = 0
    skip_count = 0
    fail_count = 0

    for category, brands in CATEGORIES.items():
        # 检查该品类是否所有文件都已生成（断点续传）
        all_done = all(category in progress[fk] for fk in file_keys)
        if all_done:
            print(f"[跳过] 「{category}」品类的所有模板已存在")
            skip_count += 1
            continue

        print(f"\n[生成] 「{category}」品类 (品牌: {', '.join(brands)})")
        try:
            templates = generate_category(client, category, brands)

            # 分别保存到4个文件
            for fk in file_keys:
                if category not in progress.get(fk, set()):
                    save_templates(templates[fk], file_names[fk], category)
                    print(f"    -> 已保存到 {file_names[fk]}")

            success_count += 1
            print(f"  [完成] 「{category}」品类生成成功")

        except Exception as e:
            fail_count += 1
            print(f"  [失败] 「{category}」品类生成失败: {e}")
            continue

    # 汇总统计
    print("\n" + "=" * 60)
    print("生成完成!")
    print(f"  成功: {success_count} 个品类")
    print(f"  跳过: {skip_count} 个品类 (已存在)")
    print(f"  失败: {fail_count} 个品类")
    print(f"  输出目录: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
