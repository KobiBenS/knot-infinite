#!/bin/bash

echo "Testing RunPod InfiniteTalk Handler Locally"
echo "==========================================="

# Option 1: Test with API server mode (recommended for testing endpoints)
echo -e "\n1. Testing with API server mode..."
echo "Run this command to start the API server:"
echo "python runpod_handler.py --rp_serve_api"
echo ""
echo "Then in another terminal, test with curl:"
echo 'curl -X POST http://localhost:8000/runsync -H "Content-Type: application/json" -d @test_input.json'
echo ""

# Option 2: Test with direct input
echo -e "\n2. Testing with direct test input..."
echo "Run this command:"
echo 'python runpod_handler.py --test_input '"'"'{"input": {"action": "status", "job_id": "test-123"}}'"'"''
echo ""

# Option 3: Test with test file
echo -e "\n3. Testing with test file..."
echo "Run this command:"
echo "python runpod_handler.py --test_input test_input.json"
echo ""

# Option 4: Build and test with Docker locally
echo -e "\n4. Testing with Docker (full environment)..."
echo "Build the Docker image:"
echo "docker build -t infinitetalk-test ."
echo ""
echo "Run the container with test mode:"
echo 'docker run --rm --gpus all -v $(pwd)/test_input.json:/test_input.json infinitetalk-test python /workspace/runpod_handler.py --test_input /test_input.json'
echo ""

# Option 5: Using docker-compose for local testing
echo -e "\n5. Testing with docker-compose..."
echo "docker-compose up --build"