from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    aws_endpoint: str = Field(..., alias="AWS_ENDPOINT")
    s3_bucket: str = Field(..., alias="S3_BUCKET")
    sqs_queue_url: str = Field(..., alias="SQS_QUEUE_URL")
    rag_service_url: str = Field(..., alias="RAG_SERVICE_URL")
    cache_host: str = Field("memcached", alias="CACHE_HOST")
    cache_port: int = Field(11211, alias="CACHE_PORT")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
