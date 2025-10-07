from io import BytesIO
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

client = TestClient(app)


def create_test_image(width=800, height=600):
    img = Image.new("RGB", (width, height), color="red")
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    buffer.seek(0)
    return buffer


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("app.routes.uploads.upload_image")
@patch("app.routes.uploads.send_message")
async def test_upload_endpoint_success(mock_send_message, mock_upload_image):
    mock_upload_image.return_value = {
        "s3_key": "test_project/year=2024/month=10/day=07/abc123.jpg",
        "md5_key": "test_project/year=2024/month=10/day=07/abc123.jpg.md5",
        "md5_hash": "test_hash",
    }
    mock_send_message.return_value = None

    image_file = create_test_image()

    response = client.post(
        "/projects/upload", data={"project_id": "test_project"}, files={"file": ("test.jpg", image_file, "image/jpeg")}
    )

    assert response.status_code == 200
    data = response.json()
    assert "s3_key" in data
    assert "md5_key" in data
    assert data["s3_key"].startswith("test_project/")


@patch("app.routes.uploads.upload_image")
@patch("app.routes.uploads.send_message")
async def test_upload_endpoint_validates_project_id(mock_send_message, mock_upload_image):
    image_file = create_test_image()

    response = client.post("/projects/upload", files={"file": ("test.jpg", image_file, "image/jpeg")})

    assert response.status_code == 422


@patch("app.routes.queries.ask_rag")
@patch("app.routes.queries.get_cache")
@patch("app.routes.queries.set_cache")
async def test_query_endpoint_cache_miss(mock_set_cache, mock_get_cache, mock_ask_rag):
    mock_get_cache.return_value = None
    mock_ask_rag.return_value = {"summary": "Test summary", "changes": ["change1", "change2"], "confidence": 0.95}

    response = client.post("/query", json={"project_id": "test_project", "question": "What changed?"})

    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "Test summary"
    assert len(data["changes"]) == 2
    assert data["confidence"] == 0.95


@patch("app.routes.queries.get_cache")
async def test_query_endpoint_cache_hit(mock_get_cache):
    cached_response = '{"summary":"Cached summary","changes":["cached_change"],"confidence":0.9}'
    mock_get_cache.return_value = cached_response

    response = client.post("/query", json={"project_id": "test_project", "question": "What changed?"})

    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "Cached summary"
    assert data["changes"] == ["cached_change"]


def test_query_endpoint_validation():
    response = client.post("/query", json={"project_id": "test_project"})
    assert response.status_code == 422

    response = client.post("/query", json={"question": "What changed?"})
    assert response.status_code == 422
