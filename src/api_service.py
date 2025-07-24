import os
import subprocess
import uuid
from typing import Optional

from dotenv import load_dotenv
from fastapi import Body, FastAPI
from fastapi.responses import FileResponse

import dlhm_types

app = FastAPI()
load_dotenv("local.env")

EXPERIMENT_PATH = os.getenv("EXPERIMENT_PATH")
DEFAULT_OUTPUT_DIR = os.path.join(os.getcwd(), "output")
if not os.path.exists(DEFAULT_OUTPUT_DIR):
    os.makedirs(DEFAULT_OUTPUT_DIR)


@app.get("/alive")
async def alive() -> str:
    return "Service is living the dream and hopefully doing well"


@app.post("/generate", response_class=FileResponse)
async def generate(
    description: dlhm_types.MotionDescription, model: Optional[dlhm_types.ModelInput] = Body(default=None)
) -> FileResponse:
    if not description.data:
        raise ValueError("Motion description data cannot be empty")

    request_id: str = str(uuid.uuid4())
    path = os.path.join(DEFAULT_OUTPUT_DIR, f"{request_id}.mp4")

    text_inputs = []
    dur_inputs = []
    for a, b in description.data:
        text_inputs.append(a)
        dur_inputs.append(b)

    command = [
        "python",
        "interact_teach.py",
        f"folder={EXPERIMENT_PATH}",
        "output=/hm_output",
        'texts=["' + '", "'.join(text_inputs) + '"]',
        "durs=[" + ", ".join(map(str, dur_inputs)) + "]",
    ]

    result = subprocess.run(
        command, cwd=os.path.join(os.getcwd(), "..", "teach_hm"), capture_output=True, text=True, check=False
    )
    print("Command result:", result)
    return FileResponse(path, media_type="video/mp4", filename="result.mp4")
