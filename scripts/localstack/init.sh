#!/bin/bash

set -e

echo "Initializing LocalStack resources..."

# Create S3 bucket
awslocal s3 mb s3://mss-metro-images 2>/dev/null || echo "S3 bucket already exists"
awslocal s3api put-bucket-cors --bucket mss-metro-images --cors-configuration '{
  "CORSRules": [{
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 3000
  }]
}'

# Create SQS queue
awslocal sqs create-queue --queue-name image-processing 2>/dev/null || echo "SQS queue already exists"

# Get queue URL
QUEUE_URL=$(awslocal sqs get-queue-url --queue-name image-processing --query 'QueueUrl' --output text)

echo "LocalStack resources initialized:"
echo "  - S3 Bucket: mss-metro-images"
echo "  - SQS Queue: $QUEUE_URL"
echo "Ready for development!"
