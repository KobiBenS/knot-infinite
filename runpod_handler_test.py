import os
import json
import uuid
import time
from pathlib import Path
import runpod
from typing import Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Storage paths
JOB_STORAGE_PATH = "/tmp/jobs"
OUTPUT_STORAGE_PATH = "/tmp/outputs"

os.makedirs(JOB_STORAGE_PATH, exist_ok=True)
os.makedirs(OUTPUT_STORAGE_PATH, exist_ok=True)

# In-memory job tracking for testing
jobs_status = {}

# Skip model loading for testing
model_loaded = True

def load_models():
    """Mock model loading for testing"""
    global model_loaded
    logger.info("Skipping model loading in test mode")
    model_loaded = True

def generate_video(job_input: Dict[str, Any]) -> Dict[str, Any]:
    """Mock video generation for testing"""
    job_id = str(uuid.uuid4())

    # Update job status
    jobs_status[job_id] = {
        "status": "in_progress",
        "started_at": time.time(),
        "progress": 0
    }

    # Validate required inputs
    audio_url = job_input.get("audio_url") or job_input.get("audio_path")
    image_url = job_input.get("image_url") or job_input.get("image_path")

    if not audio_url or not image_url:
        jobs_status[job_id] = {
            "status": "failed",
            "error": "Missing audio_url/audio_path or image_url/image_path",
            "failed_at": time.time()
        }
        return {
            "job_id": job_id,
            "status": "failed",
            "error": "Missing required inputs"
        }

    # Mock processing delay
    logger.info(f"Mock processing job {job_id}")
    logger.info(f"Audio: {audio_url}")
    logger.info(f"Image: {image_url}")
    logger.info(f"Size: {job_input.get('size', 'infinitetalk-480')}")

    # Mock output path
    output_path = f"{OUTPUT_STORAGE_PATH}/{job_id}.mp4"

    # Create mock output file
    Path(output_path).touch()

    # Update job status to completed
    jobs_status[job_id] = {
        "status": "completed",
        "output_path": output_path,
        "presigned_url": f"https://mock-s3.example.com/{job_id}.mp4",
        "completed_at": time.time()
    }

    return {
        "job_id": job_id,
        "status": "completed",
        "output_path": output_path,
        "presigned_url": f"https://mock-s3.example.com/{job_id}.mp4"
    }

def check_status(job_input: Dict[str, Any]) -> Dict[str, Any]:
    """Check the status of a generation job"""
    job_id = job_input.get("job_id")

    if not job_id:
        return {"error": "job_id is required"}

    if job_id not in jobs_status:
        # Mock some test job IDs
        if job_id == "test-123":
            return {
                "job_id": job_id,
                "status": "in_progress",
                "progress": 50,
                "message": "Processing video..."
            }
        elif job_id == "test-completed":
            return {
                "job_id": job_id,
                "status": "completed",
                "output_path": "/tmp/outputs/test-completed.mp4",
                "presigned_url": "https://mock-s3.example.com/test-completed.mp4"
            }
        return {"error": "Job not found"}

    return jobs_status[job_id]

def get_output(job_input: Dict[str, Any]) -> Dict[str, Any]:
    """Get the output file of a completed job"""
    job_id = job_input.get("job_id")

    if not job_id:
        return {"error": "job_id is required"}

    # Handle test job IDs
    if job_id == "test-completed":
        return {
            "job_id": job_id,
            "status": "completed",
            "download_url": "https://mock-s3.example.com/test-completed.mp4",
            "local_path": "/tmp/outputs/test-completed.mp4"
        }

    if job_id not in jobs_status:
        return {"error": "Job not found"}

    job_info = jobs_status[job_id]

    if job_info["status"] != "completed":
        return {"error": f"Job is not completed. Current status: {job_info['status']}"}

    return {
        "job_id": job_id,
        "status": "completed",
        "download_url": job_info.get("presigned_url"),
        "local_path": job_info.get("output_path")
    }

def handler(job):
    """Main RunPod handler function"""
    job_input = job["input"]
    action = job_input.get("action", "generate")

    logger.info(f"Handling action: {action}")
    logger.info(f"Input: {json.dumps(job_input, indent=2)}")

    if action == "generate":
        return generate_video(job_input)
    elif action == "status":
        return check_status(job_input)
    elif action == "get_output":
        return get_output(job_input)
    else:
        return {"error": f"Unknown action: {action}"}

if __name__ == "__main__":
    logger.info("Starting RunPod test handler...")
    runpod.serverless.start({"handler": handler})