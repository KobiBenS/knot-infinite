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

# Copy handler and entrypoint
COPY runpod_handler.py /workspace/
COPY entrypoint.sh /workspace/

RUN chmod +x /workspace/entrypoint.sh

# Set environment variables
ENV HF_HOME=/runpod-volume/huggingface
ENV TORCH_HOME=/runpod-volume/torch
ENV MODEL_DIR=/runpod-volume/models

WORKDIR /workspace

CMD ["/workspace/entrypoint.sh"]