#!/bin/bash
set -e

IMAGE_NAME=rag_dei_chatbot
CONTAINER_NAME=rag_dei_chatbot
VOLUME_NAME=rag_dei_model_cache

# Build Docker image
echo "🔨 Building Docker image..."
docker build -t $IMAGE_NAME .

# Stop and remove existing container if exists
if docker ps -a --format '{{.Names}}' | grep -Eq "^${CONTAINER_NAME}\$"; then
    echo "🧹 Removing old container..."
    docker stop $CONTAINER_NAME
    docker rm $CONTAINER_NAME
fi

# Create Docker volume if it doesn't exist
if ! docker volume ls --format '{{.Name}}' | grep -Eq "^${VOLUME_NAME}\$"; then
    echo "💾 Creating Docker volume '$VOLUME_NAME'..."
    docker volume create $VOLUME_NAME
fi

# Run Docker container with named volume
echo "🚀 Starting container..."
docker run -d \
  --name $CONTAINER_NAME \
  -p 8001:8001 \
  -v $VOLUME_NAME:/root/.cache \
  $IMAGE_NAME

echo "✅ Container started successfully. Access the app at http://localhost:8001"
