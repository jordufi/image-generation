from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import websocket
import requests
import uuid
import json
import os
from pathlib import Path
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="ComfyUI Diffusion API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_config():
    with open("config.json", "r") as f:
        return json.load(f)


def get_comfyui_address():
    """Get ComfyUI address from environment variable or config file."""
    env_address = os.getenv("COMFYUI_ADDRESS")
    if env_address:
        return env_address
    config = load_config()
    return config["comfyui_backend"]


def establish_connection(server_address):
    client_id = str(uuid.uuid4())
    ws = websocket.WebSocket()
    ws.connect(f"ws://{server_address}/ws?clientId={client_id}")
    return ws, client_id


def send_workflow(server_address, client_id, workflow):
    payload = {"prompt": workflow, "client_id": client_id}
    return requests.post(f"http://{server_address}/prompt", json=payload)


def download_image(server_address, filename, subfolder, output_dir):
    url = f"http://{server_address}/view"
    params = {"filename": filename, "subfolder": subfolder, "type": "output"}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "wb") as f:
            f.write(response.content)
        return filepath
    return None


def update_prompt(workflow, prompt, negative_text, steps, cfg):
    workflow["16"]["inputs"]["text"] = prompt
    workflow["40"]["inputs"]["text"] = negative_text
    workflow["3"]["inputs"]["steps"] = steps
    workflow["3"]["inputs"]["cfg"] = cfg
    return workflow


class GenerateRequest(BaseModel):
    prompt: str = "A tiny tiny dinosaur"
    negative_prompt: str = ""
    steps: int = 10
    cfg: float = 4


@app.post("/generate")
def generate_image(request: GenerateRequest):
    """Generate an image with ComfyUI and return the resulting file."""
    config = load_config()
    server = get_comfyui_address()

    ws, client_id = establish_connection(server)
    with open(config["workflow_file"], "r") as f:
        workflow = json.load(f)

    workflow = update_prompt(
        workflow,
        request.prompt,
        request.negative_prompt,
        request.steps,
        request.cfg
    )

    r = send_workflow(server, client_id, workflow)
    if r.status_code != 200:
        raise HTTPException(status_code=500, detail="Error sending workflow to ComfyUI")

    output_path = None
    while True:
        msg = ws.recv()
        data = json.loads(msg)
        if data.get("type") == "executed":
            images = data.get("data", {}).get("output", {}).get("images", [])
            if not images:
                raise HTTPException(status_code=500, detail="No image generated")
            img = images[0]
            output_path = download_image(server, img["filename"], img.get("subfolder", ""), config["output_dir"])
            break

    if not output_path:
        raise HTTPException(status_code=500, detail="Failed to download image")

    return FileResponse(output_path, media_type="image/png")
