# Use specific version of nvidia cuda image
FROM nvidia/cuda:12.8.0-cudnn-devel-ubuntu22.04 as runtime

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}

WORKDIR /workspace

# Install system dependencies
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
    build-essential \
    ninja-build \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python
RUN ln -sf /usr/bin/python3.10 /usr/bin/python && \
    ln -sf /usr/bin/python3.10 /usr/bin/python3 && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

# Upgrade pip (root is fine in Docker)
RUN pip install --upgrade --root-user-action=ignore pip setuptools wheel

# Install PyTorch with CUDA 12.4 support (compatible with CUDA 12.8)
RUN pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu124

# Copy and install RunPod requirements
COPY requirements_runpod.txt .
RUN pip install -r requirements_runpod.txt

# Clone InfiniteTalk repository
RUN git clone https://github.com/MeiGen-AI/InfiniteTalk.git /workspace/InfiniteTalk

# Install InfiniteTalk requirements
WORKDIR /workspace/InfiniteTalk
RUN pip install -r requirements.txt

# Install xformers for CUDA 12.x (compatible with CUDA 12.8)
RUN pip install xformers==0.0.28.post3 --index-url https://download.pytorch.org/whl/cu124

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

# Note: WAN model needs to be downloaded separately due to size
# Add download command here when you have the model URL

# Copy handler and entrypoint
COPY runpod_handler.py /workspace/
COPY entrypoint.sh /workspace/

RUN chmod +x /workspace/entrypoint.sh

# Set environment variables - models in image, outputs to volume/tmp
ENV HF_HOME=/workspace/.cache/huggingface
ENV TORCH_HOME=/workspace/.cache/torch
ENV MODEL_DIR=/workspace/models
ENV OUTPUT_DIR=/tmp/outputs
ENV PYTHONPATH=/workspace/InfiniteTalk:$PYTHONPATH

WORKDIR /workspace

CMD ["/workspace/entrypoint.sh"]