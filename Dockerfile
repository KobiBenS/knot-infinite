# InfiniteTalk RunPod v2.0 - Force rebuild Sep 2025
FROM nvidia/cuda:12.8.0-cudnn-devel-ubuntu22.04

# Cache bust to force rebuild - update this to force new build
ARG CACHEBUST=v3.0-complete-fix

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}

WORKDIR /workspace

# Install system dependencies including all audio/video libraries
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    wget \
    git \
    ffmpeg \
    libsm6 \
    libxext6 \
    libglib2.0-0 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    sox \
    libsox-dev \
    libsox-fmt-all \
    libsndfile1 \
    libsndfile1-dev \
    portaudio19-dev \
    build-essential \
    ninja-build \
    espeak-ng \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python
RUN ln -sf /usr/bin/python3.10 /usr/bin/python && \
    ln -sf /usr/bin/python3.10 /usr/bin/python3 && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

# Upgrade pip (root is fine in Docker)
RUN pip install --upgrade pip setuptools wheel

# Install PyTorch - using the exact version from docs
# torch==2.4.1 with CUDA 12.1 as specified
RUN pip install torch==2.4.1 torchvision==0.19.1 torchaudio==2.4.1 --index-url https://download.pytorch.org/whl/cu121

# Copy and install RunPod requirements
COPY requirements_runpod.txt .
RUN pip install -r requirements_runpod.txt

# Clone InfiniteTalk repository
RUN git clone https://github.com/MeiGen-AI/InfiniteTalk.git /workspace/InfiniteTalk

# Install InfiniteTalk requirements
WORKDIR /workspace/InfiniteTalk
RUN pip install -r requirements.txt

# Install xformers FIRST (from docs) - version 0.0.28 with CUDA 12.1
RUN pip install -U xformers==0.0.28 --index-url https://download.pytorch.org/whl/cu121

# CRITICAL: Install all dependencies BEFORE flash_attn (exact order from docs)
# Step 1: Install misaki with English support
RUN pip install misaki[en]

# Step 2: Install build dependencies required for flash_attn
RUN pip install ninja
RUN pip install psutil
RUN pip install packaging
RUN pip install wheel

# Step 3: NOW install flash_attn after all dependencies are in place
RUN pip install flash_attn==2.7.4.post1 || echo "Flash attention installation failed, continuing..."

# Install librosa and other audio dependencies
RUN pip install librosa soundfile espeak-phonemizer

# Install kokoro if it's a separate package
RUN pip install kokoro || echo "Kokoro might be part of InfiniteTalk"

# Install ParaAttention
RUN pip install git+https://github.com/chengzeyi/ParaAttention.git

# Download models during build for fast cold start
RUN mkdir -p /workspace/models/wan && \
    mkdir -p /workspace/models/infinitetalk && \
    mkdir -p /workspace/models/wav2vec2

# Install git-lfs for model downloads
RUN apt-get update && apt-get install -y git-lfs && rm -rf /var/lib/apt/lists/*

# Download Wav2Vec2 model (small, ~400MB)
RUN git lfs install && \
    git clone https://huggingface.co/facebook/wav2vec2-base /workspace/models/wav2vec2/wav2vec2-base || \
    echo "Warning: Wav2Vec2 download failed, will retry at runtime"

# Verify critical dependencies are installed
RUN python -c "import misaki; print('misaki installed successfully')" || exit 1
RUN python -c "import torch; print(f'PyTorch {torch.__version__} installed')" || exit 1
RUN python -c "import librosa; print('librosa installed successfully')" || exit 1

# Copy handler and entrypoint (v2.0 with fixes)
COPY runpod_handler.py /workspace/runpod_handler.py
COPY entrypoint.sh /workspace/entrypoint.sh

RUN chmod +x /workspace/entrypoint.sh

# Set environment variables - models in image, outputs to volume/tmp
ENV HF_HOME=/workspace/.cache/huggingface
ENV TORCH_HOME=/workspace/.cache/torch
ENV MODEL_DIR=/workspace/models
ENV OUTPUT_DIR=/tmp/outputs
ENV PYTHONPATH=/workspace/InfiniteTalk:$PYTHONPATH

WORKDIR /workspace

# Add a final check for misaki before starting
RUN echo '#!/bin/bash' > /workspace/check_deps.sh && \
    echo 'python -c "import misaki; print(\"misaki module found\")"' >> /workspace/check_deps.sh && \
    echo 'python -c "import torch; print(f\"PyTorch {torch.__version__} ready\")"' >> /workspace/check_deps.sh && \
    chmod +x /workspace/check_deps.sh

CMD ["/workspace/entrypoint.sh"]