import asyncio
import json
from typing import Any

import aioboto3

from app.core.logger import logger
from app.core.settings import settings


async def send_message(message: dict[str, Any], max_retries: int = 3) -> None:
    last_error = None

    for attempt in range(max_retries):
        try:
            async with aioboto3.client("sqs", endpoint_url=settings.aws_endpoint) as sqs:
                await sqs.send_message(
                    QueueUrl=settings.sqs_queue_url,
                    MessageBody=json.dumps(message)
                )
                logger.info("message_enqueued", queue=settings.sqs_queue_url, attempt=attempt + 1)
                return
        except Exception as e:
            last_error = e
            logger.warning(
                "sqs_send_failed",
                attempt=attempt + 1,
                max_retries=max_retries,
                error=str(e)
            )
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)

    error_msg = f"Failed to send SQS message after {max_retries} retries"
    logger.error("sqs_send_exhausted", max_retries=max_retries, error=str(last_error))
    raise Exception(error_msg) from last_error
