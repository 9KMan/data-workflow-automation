"""Tests for health endpoints."""
import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    def test_root(self, test_client):
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data

    def test_health_check(self, test_client):
        response = test_client.get("/api/v1/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "database" in data

    def test_pipeline_health_empty(self, test_client):
        response = test_client.get("/api/v1/health/pipeline")
        assert response.status_code == 200
        data = response.json()
        assert data["total_runs"] == 0
        assert data["success_rate"] == 1.0
