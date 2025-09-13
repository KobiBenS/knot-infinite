#!/bin/bash

echo "Starting InfiniteTalk RunPod Handler..."

# No volume needed - using /tmp for temporary outputs
mkdir -p /tmp/outputs
mkdir -p /tmp/jobs

echo "Configuration:"
echo "  Models: /workspace/models (baked in image)"
echo "  Temp outputs: /tmp/outputs"
echo "  S3 bucket: ${BUCKET_NAME:-not configured}"
echo "  GPU availability: Maximum (no volume constraints)"

# Verify models exist in image
if [ -d "/workspace/models/wav2vec2/wav2vec2-base" ]; then
    echo "✓ Wav2Vec2 model found"
else
    echo "⚠ Wav2Vec2 model not found in image"
fi

if [ -d "/workspace/models/wan" ]; then
    echo "✓ WAN model directory found"
else
    echo "⚠ WAN model directory not found in image"
fi

cd /workspace

python -u runpod_handler.py