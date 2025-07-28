import os
import subprocess
import uuid
from typing import Optional

from dotenv import load_dotenv
from fastapi import Body, FastAPI
from fastapi.responses import FileResponse

from model_handler import ModelHandler
import dlhm_types

app = FastAPI()
load_dotenv("local.env")
mh = ModelHandler()

EXPERIMENT_PATH = os.getenv("EXPERIMENT_PATH")
DEFAULT_OUTPUT_DIR = os.path.join(os.getcwd(), "output")
if not os.path.exists(DEFAULT_OUTPUT_DIR):
    os.makedirs(DEFAULT_OUTPUT_DIR)


@app.get("/alive")
async def alive() -> str:
    return "Service is living the dream and hopefully doing well"


# @app.post("/upload", respone_class)


@app.post("/generate/")
async def generate(motion_description: str, durations: list[float], model_id: str):
    


# @app.get("/status")


# @app.get("/download/{file_id}")
