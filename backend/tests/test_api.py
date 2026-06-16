import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "抖音电商竞品智能分析与AI素材工厂 API"

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_dashboard_stats():
    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data

def test_hot_products():
    response = client.get("/api/v1/products/hot?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "products" in data["data"]

def test_review_analysis():
    response = client.get("/api/v1/reviews/analysis")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
