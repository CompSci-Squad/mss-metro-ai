# Development Guide

## Setup

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

### Install Dependencies

```bash
# Install all dependencies including dev dependencies
uv sync --all-extras

# Install only production dependencies
uv sync
```

## Pre-commit Hooks

Pre-commit hooks are configured to run automatically before each commit. They include:
- Trailing whitespace removal
- End-of-file fixer
- YAML/JSON/TOML validation
- Ruff linting and formatting
- Mypy type checking

### Setup Pre-commit Hooks

```bash
# Install pre-commit hooks
uv run task pre-commit-install

# Or manually
uv run pre-commit install
```

### Run Pre-commit Manually

```bash
# Run all hooks on all files
uv run task pre-commit

# Or manually
uv run pre-commit run --all-files
```

### Update Pre-commit Hooks

```bash
uv run task pre-commit-update
```

## Development Tasks

This project uses `taskipy` for task management. Available tasks:

### Linting

```bash
# Check code with ruff
uv run task lint

# Auto-fix linting issues and format code
uv run task lint-fix

# Format code only
uv run task format
```

### Type Checking

```bash
# Run mypy type checker
uv run task type-check
```

### Testing

```bash
# Run tests
uv run task test

# Run tests with coverage report
uv run task test-cov
```

### Development Server

```bash
# Start development server with hot reload
uv run task dev
```

### CI Pipeline

```bash
# Run all CI checks (lint, type-check, test)
uv run task ci
```

### Cleanup

```bash
# Clean up cache and temporary files
uv run task clean
```

## Project Structure

```
.
├── app/                    # Application source code
│   ├── clients/           # External service clients (S3, SQS, RAG, etc.)
│   ├── core/              # Core configuration (settings, logger)
│   ├── routes/            # API route handlers
│   ├── schemas/           # Pydantic models
│   ├── utils/             # Utility functions
│   ├── main.py            # FastAPI application
│   └── lambda_handler.py  # AWS Lambda handler
├── tests/                 # Test files
├── scripts/               # Utility scripts
├── pyproject.toml         # Project configuration and dependencies
├── .pre-commit-config.yaml # Pre-commit hooks configuration
└── uv.lock                # Lock file for reproducible builds
```

## Dependencies

### Production Dependencies
- **aioboto3** - Async AWS SDK
- **aiohttp** - Async HTTP client
- **fastapi** - Web framework
- **mangum** - AWS Lambda adapter for ASGI applications
- **pillow** - Image processing
- **pydantic** - Data validation
- **pydantic-settings** - Settings management
- **pymemcache** - Memcache client
- **python-dotenv** - Environment variable management
- **python-multipart** - File upload support
- **python-ulid** - ULID generation
- **structlog** - Structured logging

### Dev Dependencies
- **mypy** - Static type checker
- **pre-commit** - Pre-commit hook manager
- **pytest** - Testing framework
- **pytest-asyncio** - Async test support
- **pytest-cov** - Coverage reporting
- **ruff** - Fast Python linter and formatter (replaces Black and Flake8)
- **taskipy** - Task runner

## Code Quality Standards

- **Line length**: 120 characters
- **Python version**: 3.12+
- **Import order**: Standard library → Third-party → First-party
- **Type hints**: Encouraged (mypy checks enabled)
- **Code style**: Enforced by ruff
