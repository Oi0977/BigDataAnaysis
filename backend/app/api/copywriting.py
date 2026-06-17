import uuid
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from backend.app.core.hbase_service import hbase_service
from backend.app.core.ai_service import ai_service

router = APIRouter()


class CopywritingRequest(BaseModel):
    product_id: str
    style: str = "professional"
    requirements: Optional[str] = None
    count: int = 3


@router.post("/generate")
async def generate_copywriting(request: CopywritingRequest):
    """生成AI文案"""
    try:
        # 获取商品信息
        product = hbase_service.get_product(request.product_id)
        if not product:
            return {
                "code": 404,
                "message": "商品不存在",
                "data": None
            }

        # 获取商品评价
        reviews = hbase_service.get_reviews_by_product(request.product_id)

        # 提取关键词
        keywords = []
        for review in reviews:
            keywords.extend(review['keywords'])

        # 生成文案
        copywriting_list = []
        for i in range(request.count):
            content = ai_service.generate_copywriting(
                product_info=product,
                keywords=keywords,
                style=request.style,
                requirements=request.requirements
            )

            # 持久化到 HBase
            copywriting_id = f"W{uuid.uuid4().hex[:8]}"
            try:
                hbase_service.insert_copywriting(
                    copywriting_id=copywriting_id,
                    product_id=request.product_id,
                    content=content,
                    style=request.style
                )
            except Exception as e:
                print(f"保存文案失败: {e}")

            copywriting_list.append({
                "id": copywriting_id,
                "content": content,
                "style": request.style
            })

        return {
            "code": 200,
            "message": "success",
            "data": {
                "product": product,
                "copywritingList": copywriting_list
            }
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"生成文案失败: {str(e)}",
            "data": None
        }
