#!/usr/bin/env python3
"""
Local test script for InfiniteTalk RunPod handler
Tests the handler without needing full RunPod infrastructure
"""

import sys
import json
import os
from pathlib import Path

# Mock the RunPod environment for local testing
class MockRunPod:
    class serverless:
        @staticmethod
        def start(config):
            handler = config["handler"]

            # Test different actions
            test_cases = [
                {
                    "name": "Test Status Check",
                    "input": {
                        "action": "status",
                        "job_id": "test-job-123"
                    }
                },
                {
                    "name": "Test Get Output",
                    "input": {
                        "action": "get_output",
                        "job_id": "test-job-456"
                    }
                },
                {
                    "name": "Test Generation (Mock)",
                    "input": {
                        "action": "generate",
                        "audio_url": "https://example.com/test.wav",
                        "image_url": "https://example.com/test.jpg",
                        "size": "infinitetalk-480",
                        "frame_num": 81,
                        "max_frame_num": 200
                    }
                }
            ]

            for test in test_cases:
                print(f"\n{'='*60}")
                print(f"Running: {test['name']}")
                print(f"{'='*60}")
                print(f"Input: {json.dumps(test['input'], indent=2)}")

                try:
                    result = handler({"input": test["input"]})
                    print(f"Output: {json.dumps(result, indent=2)}")
                except Exception as e:
                    print(f"Error: {str(e)}")
                    import traceback
                    traceback.print_exc()

# Replace runpod import with mock
sys.modules['runpod'] = MockRunPod()

# Now import the handler
try:
    # Modify the handler to skip model loading for testing
    os.environ['SKIP_MODEL_LOAD'] = 'true'

    # Import the handler module
    import runpod_handler

    # Patch the load_models function for testing
    original_load_models = runpod_handler.load_models
    def mock_load_models():
        print("Skipping model loading for local test...")
        runpod_handler.model_loaded = True

    runpod_handler.load_models = mock_load_models

    # Run the handler with mock RunPod
    MockRunPod.serverless.start({"handler": runpod_handler.handler})

except ImportError as e:
    print(f"Error importing handler: {e}")
    print("Make sure you're running this from the project directory")
except Exception as e:
    print(f"Unexpected error: {e}")
    import traceback
    traceback.print_exc()