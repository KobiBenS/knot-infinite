#!/bin/bash

echo "Starting InfiniteTalk RunPod Handler..."

mkdir -p /runpod-volume/models/wan
mkdir -p /runpod-volume/models/infinitetalk
mkdir -p /runpod-volume/outputs
mkdir -p /runpod-volume/jobs

if [ ! -d "/runpod-volume/models/wan/wan-infinitetalk-14B-e50" ]; then
    echo "Downloading WAN model..."
    cd /runpod-volume/models/wan
    wget -c https://huggingface.co/alibaba-models/wan-infinitetalk-14B-e50/resolve/main/model.pt -O model.pt || true
fi

if [ ! -d "/runpod-volume/models/infinitetalk/wav2vec2-base" ]; then
    echo "Downloading Wav2Vec2 model..."
    cd /runpod-volume/models/infinitetalk
    git clone https://huggingface.co/facebook/wav2vec2-base wav2vec2-base || true
fi

cd /workspace

python -u runpod_handler.py