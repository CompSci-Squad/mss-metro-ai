from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # AWS Configuration
    aws_endpoint: str = Field(..., alias="AWS_ENDPOINT")
    s3_bucket: str = Field(..., alias="S3_BUCKET")
    sqs_queue_url: str = Field(..., alias="SQS_QUEUE_URL")

    # Redis Configuration (replacing Memcached)
    redis_host: str = Field("localhost", alias="REDIS_HOST")
    redis_port: int = Field(6379, alias="REDIS_PORT")
    redis_db: int = Field(0, alias="REDIS_DB")
    redis_password: str = Field("", alias="REDIS_PASSWORD")
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")

    # Celery Configuration
    celery_broker_url: str = Field("redis://localhost:6379/0", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field("redis://localhost:6379/0", alias="CELERY_RESULT_BACKEND")

    # OpenSearch Configuration
    opensearch_host: str = Field("localhost", alias="OPENSEARCH_HOST")
    opensearch_port: int = Field(9200, alias="OPENSEARCH_PORT")
    opensearch_user: str = Field("admin", alias="OPENSEARCH_USER")
    opensearch_password: str = Field("admin", alias="OPENSEARCH_PASSWORD")
    opensearch_index: str = Field("image-embeddings", alias="OPENSEARCH_INDEX")
    opensearch_use_ssl: bool = Field(False, alias="OPENSEARCH_USE_SSL")
    opensearch_verify_certs: bool = Field(False, alias="OPENSEARCH_VERIFY_CERTS")

    # VLM Model Configuration
    vlm_model_name: str = Field("Salesforce/blip2-opt-2.7b", alias="VLM_MODEL_NAME")
    vlm_model_cache_dir: str = Field("./models", alias="VLM_MODEL_CACHE_DIR")
    embedding_model_name: str = Field("sentence-transformers/clip-ViT-B-32", alias="EMBEDDING_MODEL_NAME")
    use_quantization: bool = Field(True, alias="USE_QUANTIZATION")
    device: str = Field("cpu", alias="DEVICE")

    # Processing Configuration
    max_image_size: int = Field(1024, alias="MAX_IMAGE_SIZE")
    cache_ttl: int = Field(3600, alias="CACHE_TTL")  # 1 hour in seconds

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
