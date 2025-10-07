FROM public.ecr.aws/lambda/python:3.12 as builder

WORKDIR /build

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml ./
RUN uv pip install --system --no-cache-dir -r pyproject.toml && \
    find /var/lang/lib/python3.12/site-packages -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true && \
    find /var/lang/lib/python3.12/site-packages -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /var/lang/lib/python3.12/site-packages -name "*.pyc" -delete && \
    find /var/lang/lib/python3.12/site-packages -name "*.pyo" -delete

FROM public.ecr.aws/lambda/python:3.12

WORKDIR ${LAMBDA_TASK_ROOT}

COPY --from=builder /var/lang/lib/python3.12/site-packages /var/lang/lib/python3.12/site-packages
COPY app ./app

CMD ["app.lambda_handler.handler"]
