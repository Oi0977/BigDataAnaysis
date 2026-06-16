import pytest
from app.core.hbase_service import hbase_service
from app.core.es_service import es_service

def test_hbase_connection():
    assert hbase_service.connection is not None

def test_es_connection():
    assert es_service.client is not None

def test_insert_product():
    product = {
        'product_id': 'P000001',
        'name': '测试商品',
        'category': '手机',
        'price': 1999.0,
        'sales': 1000,
        'rating': 4.5,
        'hot_score': 1500.0,
        'image_url': 'https://example.com/test.jpg',
        'description': '测试商品描述',
        'create_time': '2024-01-01T00:00:00'
    }

    hbase_service.insert_product(product)
    result = hbase_service.get_product('P000001')
    assert result is not None
    assert result['name'] == '测试商品'
