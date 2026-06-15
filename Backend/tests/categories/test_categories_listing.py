from typing import Callable, Dict

import pytest
from fastapi.testclient import TestClient


def test_list_categories_requires_authentication(client: TestClient):
    """Test that listing categories requires authentication."""
    response = client.get("/api/categories")

    assert response.status_code == 401
    payload = response.json()
    assert "detail" in payload


def test_list_categories(client: TestClient, auth_user: Dict, category_factory: Callable[..., Dict]):
    """Test that authenticated users can list categories."""
    category_factory(name="Technology")
    category_factory(name="Arts")
    category_factory(name="Sports")

    response = client.get("/api/categories", headers=auth_user["headers"])

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["message"] == "Categories fetched successfully"
    
    categories = payload["data"]
    assert len(categories) == 3
    
    # Verify categories are sorted by name
    category_names = [cat["name"] for cat in categories]
    assert category_names == ["Arts", "Sports", "Technology"]
    
    # Verify each category has required fields
    for category in categories:
        assert "id" in category
        assert "name" in category
        assert isinstance(category["id"], str)
        assert isinstance(category["name"], str)
        assert len(category["id"]) > 0
        assert len(category["name"]) > 0


def test_list_categories_returns_empty_list_when_no_categories(client: TestClient, auth_user: Dict):
    """Test that listing categories returns empty list when no categories exist."""
    response = client.get("/api/categories", headers=auth_user["headers"])

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    categories = payload["data"]
    assert categories == []


def test_list_categories_returns_all_categories_regardless_of_events(client: TestClient, auth_user: Dict, category_factory: Callable[..., Dict]):
    """Test that all categories are returned even if they have no events."""
    category_factory(name="Unused Category")
    category_factory(name="Another Category")

    response = client.get("/api/categories", headers=auth_user["headers"])

    assert response.status_code == 200
    payload = response.json()
    categories = payload["data"]
    assert len(categories) == 2
    category_names = [cat["name"] for cat in categories]
    assert "Unused Category" in category_names
    assert "Another Category" in category_names
