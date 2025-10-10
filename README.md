# MSS Metro AI - Vision-Language Model Image Processing API

A FastAPI-based application for processing and querying images using Vision-Language Models (VLMs), vector search, and asynchronous processing. This system allows users to upload images to projects, automatically generate embeddings and captions, and query images using natural language with intelligent comparison capabilities.

## 🌟 Features

- **Multi-Image Project Management**: Upload and organize images by project with automatic chronological ordering
- **Vision-Language Model Processing**: Uses BLIP-2 for image captioning and question answering
- **Vector Search**: CLIP-based embeddings with OpenSearch for semantic image search
- **Asynchronous Processing**: Celery workers for background image processing
- **Intelligent Caching**: Redis-based caching for embeddings and query results
- **Structured Queries**: LangChain integration for structured JSON responses
- **Image Comparison**: Built-in support for comparing images and detecting changes
- **8-bit Quantization**: Optimized VLM models for CPU inference
- **Containerized Deployment**: Docker and Docker Compose setup for easy deployment

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌───────────────┐
│   FastAPI   │─────▶│    Celery    │─────▶│  VLM Service  │
│   Server    │      │   Workers    │      │   (BLIP-2)    │
└──────┬──────┘      └──────┬───────┘      └───────────────┘
       │                    │
       │                    │
       ▼                    ▼
┌─────────────┐      ┌──────────────┐
│    Redis    │      │  OpenSearch  │
│   (Cache)   │      │   (Vectors)  │
└─────────────┘      └──────────────┘
       │                    │
       │                    │
       ▼                    ▼
┌─────────────────────────────────┐
│      AWS S3 (LocalStack)        │
│       Image Storage             │
└─────────────────────────────────┘
```

### Components

1. **FastAPI Server**: REST API for image uploads and queries
2. **Celery Workers**: Asynchronous processing of images (embeddings, captions)
3. **Redis**: Message broker for Celery and caching layer
4. **OpenSearch**: Vector database for semantic search
5. **VLM Service**: BLIP-2 model for image understanding
6. **Embedding Service**: CLIP model for vector embeddings
7. **LangChain Service**: Structured query responses

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.12+ (for local development)
- 8GB+ RAM (for running VLM models)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd mss-metro-ai-api-service
```

### 2. Configure Environment

Copy and edit the environment file:

```bash
cp .env.local .env
# Edit .env with your configurations if needed
```

### 3. Start Services with Docker Compose

```bash
docker-compose up -d
```

This will start:
- FastAPI server on `http://localhost:8000`
- OpenSearch on `http://localhost:9200`
- Redis on `localhost:6379`
- LocalStack (S3) on `http://localhost:4566`
- Celery worker for async processing

### 4. Wait for Services to Initialize

```bash
# Check service health
docker-compose ps

# View logs
docker-compose logs -f api
```

## 📚 API Endpoints

### Upload Image

```bash
POST /projects/upload
Content-Type: multipart/form-data

Parameters:
- project_id: string (Project identifier)
- file: file (Image file)

Response:
{
  "image_id": "01HXXX...",
  "project_id": "my-project",
  "s3_key": "my-project/01HXXX.../image.jpg",
  "sequence_number": 1,
  "task_id": "celery-task-id",
  "status": "processing",
  "upload_url": "s3://..."
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/projects/upload" \
  -F "project_id=my-project" \
  -F "file=@/path/to/image.jpg"
```

### Query Images

```bash
POST /query
Content-Type: application/json

Body:
{
  "project_id": "my-project",
  "question": "What changes can you see in the images?",
  "sequence_number": null,  // Optional: query specific image
  "comparison_sequences": [1, 2],  // Optional: compare specific images
  "use_vector_search": true
}

Response:
{
  "summary": "Based on the images...",
  "details": "Detailed analysis...",
  "changes": [
    {
      "type": "addition",
      "description": "New elements detected...",
      "confidence": 0.85
    }
  ],
  "relevant_images": [
    {
      "image_id": "01HXXX...",
      "sequence_number": 1,
      "s3_key": "...",
      "filename": "image.jpg",
      "description": "A photo of...",
      "relevance_score": 0.92
    }
  ],
  "confidence": 0.85,
  "metadata": {
    "images_searched": 5
  }
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "my-project",
    "question": "What is in the latest image?"
  }'
```

### Compare Images

```bash
POST /compare
Content-Type: application/json

Body:
{
  "project_id": "my-project",
  "sequence_1": 1,
  "sequence_2": 2,
  "question": "What are the differences?"
}
```

### List Project Images

```bash
GET /projects/{project_id}/images?limit=100

Response:
{
  "project_id": "my-project",
  "images": [...],
  "count": 10
}
```

### Get Image Details

```bash
GET /images/{image_id}
```

### Health Check

```bash
GET /health
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# VLM Model (default: Salesforce/blip2-opt-2.7b)
VLM_MODEL_NAME=Salesforce/blip2-opt-2.7b

# Embedding Model (default: sentence-transformers/clip-ViT-B-32)
EMBEDDING_MODEL_NAME=sentence-transformers/clip-ViT-B-32

# Enable 8-bit quantization for CPU
USE_QUANTIZATION=true

# Device: cpu or cuda
DEVICE=cpu

# Maximum image size for processing
MAX_IMAGE_SIZE=1024

# Cache TTL in seconds
CACHE_TTL=3600
```

## 🛠️ Development

### Local Development Setup

1. **Install dependencies:**

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install -r pyproject.toml
```

2. **Start infrastructure services:**

```bash
# Start only infrastructure (Redis, OpenSearch, LocalStack)
docker-compose up -d redis opensearch localstack
```

3. **Run FastAPI server:**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. **Run Celery worker:**

```bash
celery -A app.celery_app worker --loglevel=info
```

### Code Quality

```bash
# Linting
task lint

# Format code
task format

# Type checking
task type-check

# Run tests
task test

# Run all checks
task ci
```

## 🐳 Docker Deployment

### Build and Run

```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Scaling Celery Workers

```bash
docker-compose up -d --scale celery-worker=4
```

## 📊 Monitoring

### Check Service Status

```bash
# API health
curl http://localhost:8000/health

# OpenSearch health
curl http://localhost:9200/_cluster/health

# Redis info
docker exec redis redis-cli info
```

### View Logs

```bash
# API logs
docker-compose logs -f api

# Celery worker logs
docker-compose logs -f celery-worker

# All services
docker-compose logs -f
```

## 🔬 How It Works

### Image Upload Flow

1. User uploads image via POST `/projects/upload`
2. Image stored in S3 (LocalStack)
3. OpenSearch sequence number assigned
4. Celery task queued for processing
5. Worker downloads image from S3
6. VLM generates caption
7. CLIP generates embedding vector
8. Results cached in Redis
9. Metadata stored in OpenSearch

### Query Flow

1. User submits query via POST `/query`
2. Check Redis cache for existing results
3. Generate query embedding (if vector search enabled)
4. Search OpenSearch for similar images
5. LangChain structures the response
6. Cache results in Redis
7. Return structured JSON response

## 🚢 AWS ECS Deployment

For production deployment on AWS ECS with Fargate:

1. **Build and push Docker image:**

```bash
# Build for production
docker build -t mss-metro-ai:latest .

# Tag for ECR
docker tag mss-metro-ai:latest <account-id>.dkr.ecr.<region>.amazonaws.com/mss-metro-ai:latest

# Push to ECR
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/mss-metro-ai:latest
```

2. **Update environment variables** in ECS task definition
3. **Configure AWS services:**
   - Amazon OpenSearch Service
   - ElastiCache for Redis
   - S3 for image storage
   - ALB for load balancing

## 🧪 Testing

### Run Tests

```bash
pytest tests/ -v
```

### Test Coverage

```bash
task test-cov
```

## 📝 License

See LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please submit pull requests or open issues.

## 📖 Additional Documentation

- [Development Guide](DEVELOPMENT.md)
- [API Documentation](http://localhost:8000/docs) (when running)
- [Architecture Details](docs/architecture.md)
