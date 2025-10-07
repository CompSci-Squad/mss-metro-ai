from io import BytesIO

from PIL import Image

from app.utils.helpers import calculate_md5, compress_image, generate_md5_key, generate_s3_key


def test_generate_s3_key():
    project_id = "test_project"
    key = generate_s3_key(project_id, "jpg")

    assert key.startswith(f"{project_id}/year=")
    assert "/month=" in key
    assert "/day=" in key
    assert key.endswith(".jpg")

    parts = key.split("/")
    assert len(parts) == 4
    assert parts[0] == project_id


def test_generate_s3_key_different_extension():
    key = generate_s3_key("proj1", "png")
    assert key.endswith(".png")


def test_generate_md5_key():
    s3_key = "project/year=2024/month=10/day=07/abc123.jpg"
    md5_key = generate_md5_key(s3_key)
    assert md5_key == f"{s3_key}.md5"


def test_calculate_md5():
    data = b"test data"
    md5_hash = calculate_md5(data)
    assert len(md5_hash) == 32
    assert md5_hash == "eb733a00c0c9d336e65691a37ab54293"


def test_compress_image():
    img = Image.new("RGB", (2000, 2000), color="red")
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    original_data = buffer.getvalue()

    compressed = compress_image(original_data)

    assert len(compressed) < len(original_data)

    compressed_img = Image.open(BytesIO(compressed))
    assert compressed_img.size[0] <= 1920
    assert compressed_img.size[1] <= 1080


def test_compress_image_rgba():
    img = Image.new("RGBA", (1000, 1000), color=(255, 0, 0, 128))
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    original_data = buffer.getvalue()

    compressed = compress_image(original_data)

    compressed_img = Image.open(BytesIO(compressed))
    assert compressed_img.mode == "RGB"


def test_compress_image_small():
    img = Image.new("RGB", (800, 600), color="blue")
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    original_data = buffer.getvalue()

    compressed = compress_image(original_data)

    compressed_img = Image.open(BytesIO(compressed))
    assert compressed_img.size == (800, 600)
