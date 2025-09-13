#!/usr/bin/env python3
"""
Test client for InfiniteTalk RunPod serverless endpoint
"""

import os
import sys
import json
import time
import argparse
import requests
from typing import Optional, Dict, Any

import runpod


class InfiniteTalkClient:
    def __init__(self, endpoint_id: str, api_key: Optional[str] = None):
        """Initialize the InfiniteTalk client"""
        self.endpoint_id = endpoint_id
        runpod.api_key = api_key or os.environ.get("RUNPOD_API_KEY")
        self.endpoint = runpod.Endpoint(endpoint_id)

    def generate_video(
        self,
        audio_url: str,
        image_url: str,
        size: str = "infinitetalk-480",
        frame_num: int = 81,
        max_frame_num: int = 1000,
        sample_steps: int = 40,
        cfg_scale: float = 1.1,
        seed: int = -1
    ) -> Dict[str, Any]:
        """Start video generation"""

        payload = {
            "action": "generate",
            "audio_url": audio_url,
            "image_url": image_url,
            "size": size,
            "frame_num": frame_num,
            "max_frame_num": max_frame_num,
            "sample_steps": sample_steps,
            "cfg_scale": cfg_scale,
            "seed": seed
        }

        print(f"Starting video generation with payload: {json.dumps(payload, indent=2)}")

        run_request = self.endpoint.run(payload)

        print(f"Job submitted. Request ID: {run_request.id}")

        result = run_request.output(timeout=600)

        return result

    def check_status(self, job_id: str) -> Dict[str, Any]:
        """Check the status of a job"""

        payload = {
            "action": "status",
            "job_id": job_id
        }

        run_request = self.endpoint.run_sync(payload, timeout=10)
        return run_request

    def get_output(self, job_id: str) -> Dict[str, Any]:
        """Get the output of a completed job"""

        payload = {
            "action": "get_output",
            "job_id": job_id
        }

        run_request = self.endpoint.run_sync(payload, timeout=10)
        return run_request

    def generate_and_wait(
        self,
        audio_url: str,
        image_url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate video and wait for completion"""

        result = self.generate_video(audio_url, image_url, **kwargs)

        if "error" in result:
            print(f"Error during generation: {result['error']}")
            return result

        job_id = result.get("job_id")
        if not job_id:
            print("No job_id returned")
            return result

        print(f"Job {job_id} started. Waiting for completion...")

        max_wait = 1800
        start_time = time.time()

        while time.time() - start_time < max_wait:
            status_result = self.check_status(job_id)

            status = status_result.get("status")
            print(f"Status: {status}")

            if status == "completed":
                print("Video generation completed!")
                output_result = self.get_output(job_id)
                return output_result
            elif status == "failed":
                print(f"Generation failed: {status_result.get('error')}")
                return status_result

            time.sleep(10)

        print("Timeout waiting for generation to complete")
        return {"error": "Timeout"}


def main():
    parser = argparse.ArgumentParser(description="Test InfiniteTalk RunPod endpoint")
    parser.add_argument("--endpoint-id", required=True, help="RunPod endpoint ID")
    parser.add_argument("--api-key", help="RunPod API key (or use RUNPOD_API_KEY env var)")
    parser.add_argument("--audio-url", required=True, help="URL to audio file")
    parser.add_argument("--image-url", required=True, help="URL to image file")
    parser.add_argument("--size", default="infinitetalk-480", choices=["infinitetalk-480", "infinitetalk-720"])
    parser.add_argument("--frame-num", type=int, default=81, help="Frames per clip")
    parser.add_argument("--max-frame-num", type=int, default=1000, help="Max total frames")
    parser.add_argument("--sample-steps", type=int, default=40, help="Sampling steps")
    parser.add_argument("--cfg-scale", type=float, default=1.1, help="CFG scale")
    parser.add_argument("--seed", type=int, default=-1, help="Random seed (-1 for random)")

    args = parser.parse_args()

    client = InfiniteTalkClient(args.endpoint_id, args.api_key)

    result = client.generate_and_wait(
        audio_url=args.audio_url,
        image_url=args.image_url,
        size=args.size,
        frame_num=args.frame_num,
        max_frame_num=args.max_frame_num,
        sample_steps=args.sample_steps,
        cfg_scale=args.cfg_scale,
        seed=args.seed
    )

    print("\nFinal result:")
    print(json.dumps(result, indent=2))

    if "download_url" in result:
        print(f"\nDownload URL: {result['download_url']}")


if __name__ == "__main__":
    main()