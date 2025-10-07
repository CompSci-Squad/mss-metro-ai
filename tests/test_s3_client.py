import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from io import BytesIO
from PIL import Image
from app.clients.s3_client import upload_image


def create_test_image_data(width=800, height=600):
    img = Image.new("RGB", (width, height), color="blue")
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.mark.asyncio
@patch("app.clients.s3_client.aioboto3.client")
async def test_upload_image_success(mock_aioboto3_client):
    mock_s3 = AsyncMock()
    mock_aioboto3_client.return_value.__aenter__.return_value = mock_s3
    
    image_data = create_test_image_data()
    
    result = await upload_image("test_project", image_data, "test.jpg")
    
    assert "s3_key" in result
    assert "md5_key" in result
    assert "md5_hash" in result
    assert result["s3_key"].startswith("test_project/year=")
    assert result["s3_key"].endswith(".jpg")
    assert result["md5_key"] == f"{result['s3_key']}.md5"
    assert len(result["md5_hash"]) == 32
    
    assert mock_s3.put_object.call_count == 2


@pytest.mark.asyncio
@patch("app.clients.s3_client.aioboto3.client")
async def test_upload_image_different_extension(mock_aioboto3_client):
    mock_s3 = AsyncMock()
    mock_aioboto3_client.return_value.__aenter__.return_value = mock_s3
    
    image_data = create_test_image_data()
    
    result = await upload_image("proj123", image_data, "photo.png")
    
    assert result["s3_key"].endswith(".png")


@pytest.mark.asyncio
@patch("app.clients.s3_client.aioboto3.client")
async def test_upload_image_no_extension(mock_aioboto3_client):
    mock_s3 = AsyncMock()
    mock_aioboto3_client.return_value.__aenter__.return_value = mock_s3
    
    image_data = create_test_image_data()
    
    result = await upload_image("proj456", image_data, "noextension")
    
    assert result["s3_key"].endswith(".jpg")


@pytest.mark.asyncio
@patch("app.clients.s3_client.aioboto3.client")
async def test_upload_image_compression(mock_aioboto3_client):
    mock_s3 = AsyncMock()
    mock_aioboto3_client.return_value.__aenter__.return_value = mock_s3
    
    img = Image.new("RGB", (3000, 3000), color="green")
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    large_image_data = buffer.getvalue()
    
    result = await upload_image("proj_large", large_image_data, "large.jpg")
    
    assert mock_s3.put_object.call_count == 2
    
    call_args = mock_s3.put_object.call_args_list[0]
    compressed_body = call_args[1]["Body"]
    assert len(compressed_body) < len(large_image_data)


@pytest.mark.asyncio
@patch("app.clients.s3_client.aioboto3.client")
async def test_upload_image_md5_file(mock_aioboto3_client):
    mock_s3 = AsyncMock()
    mock_aioboto3_client.return_value.__aenter__.return_value = mock_s3
    
    image_data = create_test_image_data()
    
    result = await upload_image("test_md5", image_data, "test.jpg")
    
    md5_call = mock_s3.put_object.call_args_list[1]
    assert md5_call[1]["Key"].endswith(".md5")
    assert md5_call[1]["ContentType"] == "text/plain"
    assert isinstance(md5_call[1]["Body"], bytes)
