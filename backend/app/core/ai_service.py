import httpx
from typing import Dict, Any, List, Optional
from backend.app.config import settings

class AIService:
    def __init__(self):
        self.api_key = settings.ai_api_key
        self.api_url = settings.ai_base_url
        self.model = settings.ai_model

    def generate_copywriting(
        self,
        product_info: Dict[str, Any],
        keywords: List[str],
        style: str = "professional",
        requirements: Optional[str] = None
    ) -> str:
        """生成文案"""

        # 构建提示词
        prompt = f"""你是一个专业的电商文案撰写专家。请根据以下信息生成广告文案：

商品信息：
- 名称：{product_info['name']}
- 品类：{product_info['category']}
- 品牌：{product_info.get('brand', '未知')}
- 价格：{product_info['price']}元
- 描述：{product_info.get('description', '暂无')}

用户关注点：{', '.join(set(keywords)) if keywords else '暂无'}

文案风格：{style}
{f'特殊要求：{requirements}' if requirements else ''}

请生成一段吸引人的电商广告文案，突出产品优势，解决用户痛点。"""

        # 调用API
        try:
            response = httpx.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "你是一个专业的电商文案撰写专家。"},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.8
                },
                timeout=30.0
            )

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                # 如果API调用失败，返回模板文案
                return self._generate_template_copywriting(product_info, keywords, style)

        except Exception as e:
            print(f"AI API调用失败: {e}")
            return self._generate_template_copywriting(product_info, keywords, style)

    def _generate_template_copywriting(
        self,
        product_info: Dict[str, Any],
        keywords: List[str],
        style: str
    ) -> str:
        """生成模板文案（备用方案）"""

        kw_str = ', '.join(keywords[:3]) if keywords else '品质'
        templates = {
            "professional": f"""【{product_info['name']}】品质之选

作为{product_info['category']}品类的热销商品，{product_info['name']}凭借出色的产品力赢得了众多用户的青睐。

✅ 品质保证：严格品控，品质有保障
✅ 用户认可：针对用户关注的{kw_str}等痛点，我们提供了完美解决方案

现在购买仅需{product_info['price']}元，限时优惠中！""",

            "casual": f"""姐妹们！这款{product_info['name']}真的绝了！

用了之后发现，之前担心的{kw_str}问题完全不存在！

价格也很美丽，{product_info['price']}元就能拿下，冲就完了！""",

            "emotional": f"""你是否也在为{product_info['category']}产品的{kw_str}而烦恼？

{product_info['name']}，为你而来。

我们深知用户的需求，所以专注于解决每一个痛点。

{product_info['price']}元，给你的生活带来改变。"""
        }

        return templates.get(style, templates['professional'])

# 单例实例
ai_service = AIService()
