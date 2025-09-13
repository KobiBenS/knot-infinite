# InfiniteTalk on RunPod Serverless (2x H100 GPUs)

This repository contains the RunPod serverless deployment configuration for InfiniteTalk, enabling video generation from audio and images using 2x H100 GPUs.

## Features

- **3 Endpoints**:
  1. **Generation Endpoint**: Submit audio + image for video generation
  2. **Status Check Endpoint**: Check job progress (in_progress, ready, failed)
  3. **Output Retrieval Endpoint**: Get generated MP4 file

- **Storage Options**:
  - RunPod Volume for persistent model storage
  - Optional S3 integration for output files
  - Presigned URLs for secure file access

## Prerequisites

1. RunPod account with API access
2. 2x H100 GPU allocation
3. RunPod Volume (recommended: 100GB+)
4. Optional: S3-compatible storage for outputs

## Setup

### 1. Clone Repository

```bash
git clone <your-repo>
cd knot_infinitetalk
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```env
RUNPOD_API_KEY=your_api_key
BUCKET_ENDPOINT_URL=https://s3.amazonaws.com  # Optional
BUCKET_ACCESS_KEY_ID=your_key  # Optional
BUCKET_SECRET_ACCESS_KEY=your_secret  # Optional
```

### 3. Build Docker Image

```bash
docker build -t infinitetalk-runpod:latest .
```

### 4. Push to Registry

```bash
docker tag infinitetalk-runpod:latest your-registry/infinitetalk-runpod:latest
docker push your-registry/infinitetalk-runpod:latest
```

### 5. Deploy to RunPod

Using RunPod CLI:

```bash
runpod project deploy
```

Or manually create serverless endpoint with:
- Docker image: `your-registry/infinitetalk-runpod:latest`
- GPU: 2x H100
- Volume mount: `/runpod-volume`
- Environment variables from `.env`

## API Usage

### 1. Generate Video

```python
import runpod

runpod.api_key = "your_api_key"
endpoint = runpod.Endpoint("your_endpoint_id")

# Start generation
result = endpoint.run({
    "action": "generate",
    "audio_url": "https://example.com/audio.wav",
    "image_url": "https://example.com/image.jpg",
    "size": "infinitetalk-480",  # or "infinitetalk-720"
    "frame_num": 81,
    "max_frame_num": 1000,
    "sample_steps": 40,
    "cfg_scale": 1.1,
    "seed": -1  # -1 for random
})

job_id = result["job_id"]
```

### 2. Check Status

```python
status = endpoint.run_sync({
    "action": "status",
    "job_id": job_id
})

print(status["status"])  # "in_progress", "completed", or "failed"
```

### 3. Get Output

```python
output = endpoint.run_sync({
    "action": "get_output",
    "job_id": job_id
})

download_url = output["download_url"]  # If S3 is configured
local_path = output["local_path"]  # Volume path
```

## Test Client

Use the provided test client:

```bash
python test_client.py \
    --endpoint-id YOUR_ENDPOINT_ID \
    --audio-url https://example.com/audio.wav \
    --image-url https://example.com/image.jpg \
    --size infinitetalk-480
```

## Volume Structure

```
/runpod-volume/
├── models/
│   ├── wan/                 # WAN model weights
│   └── infinitetalk/         # InfiniteTalk models
├── outputs/                  # Generated videos
├── jobs/                     # Job metadata
└── huggingface/             # HF cache
```

## Model Downloads

Models are automatically downloaded on first run:
- WAN InfiniteTalk 14B model
- Wav2Vec2 base model

To pre-download models, mount the volume and run:

```bash
cd /runpod-volume/models
# Download WAN model
wget https://huggingface.co/alibaba-models/wan-infinitetalk-14B-e50/resolve/main/model.pt

# Download Wav2Vec2
git clone https://huggingface.co/facebook/wav2vec2-base
```

## Performance

- **480p generation**: ~2-3 minutes for 5-second video
- **720p generation**: ~4-5 minutes for 5-second video
- **Max video length**: Configurable (default: 1000 frames)

## Troubleshooting

### Out of Memory
- Reduce `frame_num` or `max_frame_num`
- Use 480p instead of 720p
- Ensure 2x H100 GPUs are allocated

### Model Loading Issues
- Check volume mount at `/runpod-volume`
- Verify model files exist in `/runpod-volume/models`
- Check logs: `runpod logs <pod-id>`

### S3 Upload Failures
- Verify S3 credentials in environment
- Check bucket permissions
- Ensure bucket exists

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `RUNPOD_API_KEY` | RunPod API key | Yes |
| `BUCKET_ENDPOINT_URL` | S3 endpoint URL | No |
| `BUCKET_ACCESS_KEY_ID` | S3 access key | No |
| `BUCKET_SECRET_ACCESS_KEY` | S3 secret key | No |
| `BUCKET_NAME` | S3 bucket name | No |
| `MODEL_DIR` | Model directory path | Yes |
| `HF_HOME` | HuggingFace cache | Yes |

## License

This deployment configuration follows the original InfiniteTalk license terms.