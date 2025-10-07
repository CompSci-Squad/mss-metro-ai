from pydantic import BaseModel


class UploadRequest(BaseModel):
    project_id: str
    filename: str


class UploadResponse(BaseModel):
    upload_url: str
    s3_key: str
    md5_key: str
