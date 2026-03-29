# Image Generation API

A FastAPI-based REST API service that provides easy access to ComfyUI Stable Diffusion image generation. This service acts as a middleware between your applications and a ComfyUI backend, offering a simple HTTP interface for generating images with customizable prompts, negative prompts, step counts, and guidance scales.

## Features

- **Simple REST API** - Easy-to-use `/generate` endpoint for image generation
- **Customizable Workflows** - Use your own ComfyUI workflow (sd.json)
- **WebSocket Support** - Real-time communication with ComfyUI backend for result streaming
- **Docker-Ready** - Fully containerized with Docker and Docker Compose
- **CORS Enabled** - Cross-origin requests supported for web frontend integration
- **Environment Flexible** - Configure ComfyUI backend via environment variables or config file
- **Nginx Reverse Proxy** - Production-ready reverse proxy setup included

## Prerequisites

- **ComfyUI Backend** - A running ComfyUI instance (on your network or local machine)
- **Docker & Docker Compose** - For containerized deployment
- **Python 3.12+** - If running without Docker

## Quick Start

### Using Docker Compose (Recommended)

1. **Configure the ComfyUI address** in `docker-compose.yml`:
   ```yaml
   environment:
     - COMFYUI_ADDRESS=<YOUR_COMFYUI_IP>:8188
   ```

2. **Start the service**:
   ```bash
   docker-compose up -d
   ```

3. **The API will be available at** `http://localhost:9092`

### Manual Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure ComfyUI address** in `config.json` or set environment variable:
   ```bash
   export COMFYUI_ADDRESS=<your_comfyui_ip>:8188
   ```

3. **Run the application**:
   ```bash
   ./start.sh
   ```

## Configuration

### config.json
```json
{
  "comfyui_backend": "192.168.1.200:8188",  // ComfyUI server address
  "workflow_file": "sd.json",                 // ComfyUI workflow template
  "output_dir": "/app/outputs"               // Output directory for generated images
}
```

### Environment Variables
- `COMFYUI_ADDRESS` - Override the ComfyUI backend address (takes precedence over config.json)
- Example: `COMFYUI_ADDRESS=192.168.1.100:8188`

## API Usage

### Generate Image Endpoint

**POST** `/generate`

Generate an image using Stable Diffusion through ComfyUI.

**Request Body**:
```json
{
  "prompt": "A tiny tiny dinosaur",
  "negative_prompt": "",
  "steps": 10,
  "cfg": 4.0
}
```

**Parameters**:
- `prompt` (string, optional): The positive prompt describing what you want to generate
  - Default: `"A tiny tiny dinosaur"`
- `negative_prompt` (string, optional): What you don't want in the image
  - Default: `""`
- `steps` (integer, optional): Number of inference steps (affects quality and speed)
  - Default: `10`
- `cfg` (float, optional): Classifier-free guidance scale (higher = more adherence to prompt)
  - Default: `4.0`

**Response**:
- Returns the generated image as PNG
- Content-Type: `image/png`

**Example cURL**:
```bash
curl -X POST "http://localhost:9092/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful sunset over mountains",
    "negative_prompt": "blurry, low quality",
    "steps": 20,
    "cfg": 7.0
  }' \
  --output generated_image.png
```

**Example Python**:
```python
import requests

response = requests.post(
    "http://localhost:9092/generate",
    json={
        "prompt": "A beautiful sunset over mountains",
        "negative_prompt": "blurry, low quality",
        "steps": 20,
        "cfg": 7.0
    }
)

with open("generated_image.png", "wb") as f:
    f.write(response.content)
```

## Workflow Template (sd.json)

The `sd.json` file contains the ComfyUI workflow template. Key nodes that must be present:
- Node `16`: Text input for positive prompt
- Node `40`: Text input for negative prompt
- Node `3`: KSampler with `steps` and `cfg` parameters

You can customize this workflow to use different models, sampler types, or additional processing nodes.

## Architecture

```
Client Application
       ↓ (HTTP POST /generate)
   Nginx (Port 9092)
       ↓
   FastAPI (Port 8000)
       ↓ (WebSocket + HTTP)
ComfyUI Backend (Port 8188)
       ↓
  Generated Image
```

**Data Flow**:
1. Client sends a POST request with generation parameters
2. API updates the ComfyUI workflow with the provided prompt and settings
3. Workflow is sent to ComfyUI via HTTP
4. API connects via WebSocket to receive execution status
5. When execution completes, the generated image is downloaded
6. Image is returned to the client as PNG

## Deployment

### Docker Image

The service is containerized and includes:
- Python 3.12 slim base image
- FastAPI and Uvicorn
- Nginx reverse proxy
- All Python dependencies

**Build image**:
```bash
docker build -t image-generator:latest .
```

**Run container**:
```bash
docker run -d \
  -p 9092:9092 \
  -e COMFYUI_ADDRESS=<YOUR_IP>:8188 \
  -v ./outputs:/app/outputs \
  --restart unless-stopped \
  image-generator:latest
```

### Production Considerations

- **Nginx Reverse Proxy** - Handles port forwarding (9092 → 8000)
- **Volume Mounting** - Outputs persisted to host machine
- **Restart Policy** - Set to `unless-stopped` for automatic recovery
- **Network** - Ensure ComfyUI is accessible from the container

## Troubleshooting

### "Connection refused" to ComfyUI
- Verify ComfyUI is running and accessible at the configured address
- Check firewall rules between the API server and ComfyUI
- Test connectivity: `curl http://<COMFYUI_IP>:8188/system_stats`

### "No image generated" error
- Check the sd.json workflow file exists and is valid
- Verify the workflow node IDs match (16, 40, 3)
- Check ComfyUI logs for workflow execution errors

### Port already in use
- Change port mapping in docker-compose.yml: `"<NEW_PORT>:9092"`
- Or stop the existing service: `docker-compose down`

## Technical Stack

- **Framework**: FastAPI 0.115.2
- **Server**: Uvicorn + Nginx
- **Communication**: Requests, WebSocket-client
- **Python**: 3.12
- **Deployment**: Docker & Docker Compose

## Files Overview

- `app.py` - FastAPI application with image generation logic
- `config.json` - Configuration file for ComfyUI backend and workflow
- `sd.json` - ComfyUI workflow template
- `Dockerfile` - Container definition
- `docker-compose.yml` - Multi-container orchestration
- `nginx.conf` - Nginx reverse proxy configuration
- `start.sh` - Startup script for the container
- `requirements.txt` - Python dependencies

## Notes

- Generated images are saved to the outputs directory both in the container and mounted volume
- The service maintains WebSocket connections during image generation for real-time progress
- CORS is enabled to allow requests from web frontends
- Configuration via environment variables takes precedence over config.json
