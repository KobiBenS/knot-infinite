#!/bin/bash

echo "Setting up local test environment for InfiniteTalk RunPod Handler"
echo "=================================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install basic requirements
echo "Installing RunPod and basic dependencies..."
pip install --upgrade pip
pip install runpod boto3 botocore

echo ""
echo "Setup complete!"
echo ""
echo "To test the handler locally, you have several options:"
echo ""
echo "1. Test with RunPod's built-in API server:"
echo "   source venv/bin/activate"
echo "   python runpod_handler.py --rp_serve_api"
echo ""
echo "   Then in another terminal:"
echo '   curl -X POST http://localhost:8000/runsync -H "Content-Type: application/json" -d @test_input.json'
echo ""
echo "2. Test with direct input:"
echo "   source venv/bin/activate"
echo '   python runpod_handler.py --test_input test_input.json'
echo ""
echo "3. Test specific actions:"
echo "   source venv/bin/activate"
echo '   python runpod_handler.py --test_input '"'"'{"input": {"action": "status", "job_id": "test-123"}}'"'"''
echo ""
echo "4. Build and test with Docker (requires Docker and GPUs):"
echo "   docker build -t infinitetalk-test ."
echo '   docker run --rm --gpus all infinitetalk-test python /workspace/runpod_handler.py --test_input '"'"'{"input": {"action": "status", "job_id": "test"}}'"'"''