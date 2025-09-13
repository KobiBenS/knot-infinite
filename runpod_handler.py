import os
import json
import uuid
import time
import subprocess
from pathlib import Path
import runpod
import torch
from typing import Dict, Any, Optional
import boto3
from botocore.client import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Models are baked into image, outputs go to volume or /tmp
MODEL_DIR = "/workspace/models"

# Use volume if available, otherwise use /tmp
if os.path.exists("/runpod-volume"):
    JOB_STORAGE_PATH = "/runpod-volume/jobs"
    OUTPUT_STORAGE_PATH = "/runpod-volume/outputs"
    logger.info("Using RunPod volume for storage")
else:
    JOB_STORAGE_PATH = "/tmp/jobs"
    OUTPUT_STORAGE_PATH = "/tmp/outputs"
    logger.info("No volume detected, using /tmp (outputs won't persist)")

os.makedirs(JOB_STORAGE_PATH, exist_ok=True)
os.makedirs(OUTPUT_STORAGE_PATH, exist_ok=True)

jobs_status = {}

# Global model state
model_loaded = False

s3_client = None
if os.environ.get("BUCKET_ENDPOINT_URL"):
    s3_client = boto3.client(
        's3',
        endpoint_url=os.environ.get("BUCKET_ENDPOINT_URL"),
        aws_access_key_id=os.environ.get("BUCKET_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("BUCKET_SECRET_ACCESS_KEY"),
        config=Config(signature_version='s3v4')
    )
    BUCKET_NAME = os.environ.get("BUCKET_NAME", "infinitetalk-outputs")

def load_models():
    """Initialize InfiniteTalk models - models are already in image"""
    global model_loaded

    if model_loaded:
        return

    try:
        import sys
        sys.path.append('/workspace/InfiniteTalk')

        logger.info("Loading InfiniteTalk models from image...")
        logger.info(f"Model directory: {MODEL_DIR}")

        # Verify models exist
        wav2vec_path = f"{MODEL_DIR}/wav2vec2/wav2vec2-base"
        if os.path.exists(wav2vec_path):
            logger.info(f"✓ Wav2Vec2 model found at {wav2vec_path}")
        else:
            logger.warning(f"⚠ Wav2Vec2 model not found at {wav2vec_path}")

        model_loaded = True
        logger.info("Models loaded successfully from image")
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        raise

def generate_video(job_input: Dict[str, Any]) -> Dict[str, Any]:
    """Generate video using InfiniteTalk"""
    job_id = str(uuid.uuid4())

    jobs_status[job_id] = {
        "status": "in_progress",
        "started_at": time.time(),
        "progress": 0
    }

    try:
        audio_path = job_input.get("audio_path")
        image_path = job_input.get("image_path")

        if not audio_path or not image_path:
            if job_input.get("audio_url"):
                audio_path = f"/tmp/{job_id}_audio.wav"
                subprocess.run([
                    "wget", "-O", audio_path, job_input["audio_url"]
                ], check=True)

            if job_input.get("image_url"):
                url = job_input["image_url"]
                # Keep original extension to determine type
                ext = url.split('.')[-1].lower()
                if ext in ['mp4', 'avi', 'mov', 'webm']:
                    image_path = f"/tmp/{job_id}_input.{ext}"
                else:
                    image_path = f"/tmp/{job_id}_input.jpg"

                # Download the file
                subprocess.run([
                    "wget", "-O", image_path, url
                ], check=True)

        if not audio_path or not image_path:
            raise ValueError("Either provide audio_path/image_path or audio_url/image_url")

        output_path = f"{OUTPUT_STORAGE_PATH}/{job_id}.mp4"

        size = job_input.get("size", "infinitetalk-480")
        frame_num = job_input.get("frame_num", 81)
        max_frame_num = job_input.get("max_frame_num", 1000)
        sample_steps = job_input.get("sample_steps", 40)
        sample_shift = job_input.get("sample_shift", 7 if size == "infinitetalk-480" else 11)
        cfg_scale = job_input.get("cfg_scale", 1.1)
        seed = job_input.get("seed", -1)

        # Create input JSON for InfiniteTalk
        input_json = {
            "prompt": job_input.get("prompt", "A person is talking"),
            "cond_audio": {
                "person1": audio_path
            }
        }

        # Determine if input is image or video
        if image_path.lower().endswith(('.mp4', '.avi', '.mov', '.webm')):
            input_json["cond_video"] = image_path
            logger.info(f"Using video input: {image_path}")
        else:
            input_json["cond_image"] = image_path
            logger.info(f"Using image input: {image_path}")

        # Save input JSON
        input_json_path = f"/tmp/{job_id}_input.json"
        with open(input_json_path, 'w') as f:
            import json
            json.dump(input_json, f)

        cmd = [
            "python", "/workspace/InfiniteTalk/generate_infinitetalk.py",
            "--task", "infinitetalk-14B",
            "--ckpt_dir", f"{MODEL_DIR}/wan",
            "--infinitetalk_dir", f"{MODEL_DIR}/infinitetalk",
            "--input_json", input_json_path,
            "--save_file", output_path.replace('.mp4', ''),  # InfiniteTalk adds .mp4
            "--size", size,
            "--frame_num", str(frame_num),
            "--max_frame_num", str(max_frame_num),
            "--sample_steps", str(sample_steps),
            "--sample_shift", str(sample_shift),
            "--sample_audio_guide_scale", str(cfg_scale),
            "--base_seed", str(seed)
        ]

        logger.info(f"Running command: {' '.join(cmd)}")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="/workspace/InfiniteTalk"
        )

        stdout, stderr = process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"Generation failed: {stderr}")

        presigned_url = None
        if s3_client and os.path.exists(output_path):
            try:
                s3_key = f"outputs/{job_id}.mp4"
                s3_client.upload_file(output_path, BUCKET_NAME, s3_key)

                presigned_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
                    ExpiresIn=3600 * 24  # 24 hours
                )
            except Exception as e:
                logger.error(f"Failed to upload to S3: {e}")

        jobs_status[job_id] = {
            "status": "completed",
            "output_path": output_path,
            "presigned_url": presigned_url,
            "completed_at": time.time()
        }

        return {
            "job_id": job_id,
            "status": "completed",
            "output_path": output_path,
            "presigned_url": presigned_url
        }

    except Exception as e:
        logger.error(f"Generation failed for job {job_id}: {e}")
        jobs_status[job_id] = {
            "status": "failed",
            "error": str(e),
            "failed_at": time.time()
        }
        return {
            "job_id": job_id,
            "status": "failed",
            "error": str(e)
        }

def check_status(job_input: Dict[str, Any]) -> Dict[str, Any]:
    """Check the status of a generation job"""
    job_id = job_input.get("job_id")

    if not job_id:
        return {"error": "job_id is required"}

    if job_id not in jobs_status:
        return {"error": "Job not found"}

    return jobs_status[job_id]

def get_output(job_input: Dict[str, Any]) -> Dict[str, Any]:
    """Get the output file of a completed job"""
    job_id = job_input.get("job_id")

    if not job_id:
        return {"error": "job_id is required"}

    if job_id not in jobs_status:
        return {"error": "Job not found"}

    job_info = jobs_status[job_id]

    if job_info["status"] != "completed":
        return {"error": f"Job is not completed. Current status: {job_info['status']}"}

    output_path = job_info.get("output_path")

    if not output_path or not os.path.exists(output_path):
        return {"error": "Output file not found"}

    presigned_url = job_info.get("presigned_url")
    if presigned_url:
        return {
            "job_id": job_id,
            "status": "completed",
            "download_url": presigned_url,
            "local_path": output_path
        }

    return {
        "job_id": job_id,
        "status": "completed",
        "local_path": output_path,
        "message": "File available on volume storage"
    }

def handler(job):
    """Main RunPod handler function"""
    job_input = job["input"]
    action = job_input.get("action", "generate")

    if not model_loaded and action == "generate":
        load_models()

    if action == "generate":
        return generate_video(job_input)
    elif action == "status":
        return check_status(job_input)
    elif action == "get_output":
        return get_output(job_input)
    else:
        return {"error": f"Unknown action: {action}"}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})