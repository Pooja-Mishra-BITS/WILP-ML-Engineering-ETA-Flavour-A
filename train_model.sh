#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="ml-engineering-mini-project"
CONTAINER="ml-engineering-mini-project"

echo "Running training..."
sudo docker run --rm \
	-v "$DIR:/app" \
	-w /app \
	"$IMAGE" \
	python -m pipeline.train

echo "Running Monitoring..."
sudo docker run --rm \
	-v "$DIR:/app" \
	-w /app \
	"$IMAGE" \
	python -m pipeline.monitor

echo "Rebuilding Docker image..."
sudo docker build -t "$IMAGE" "$DIR"

echo "Rebuilding API container..."
sudo docker restart "$CONTAINER"

echo "Training, Monitoring , Rebuild and API restarted completed"

