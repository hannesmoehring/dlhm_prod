# This is the api_service that handles requests, responses and forwarding them to the model handler
# It uses FastAPI for the web service
# and dotenv for environment variable management
# The model handler is in model_handler.py


import asyncio
import os
import uuid
from typing import Optional
import tempfile
import shutil
from dotenv import load_dotenv
from fastapi import BackgroundTasks, Body, FastAPI, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

import dlhm_types
from model_handler import ModelHandler

app = FastAPI()
load_dotenv("local.env")
mh = ModelHandler()


EXPERIMENT_PATH = os.getenv("EXPERIMENT_PATH")
DEFAULT_OUTPUT_DIR = os.path.join(os.getcwd(), "output")
if not os.path.exists(DEFAULT_OUTPUT_DIR):
    os.makedirs(DEFAULT_OUTPUT_DIR)

status_store: dict[uuid.UUID, dlhm_types.RequestStatus] = {}


# Health check endpoint
@app.get("/alive")
async def alive() -> str:
    return "Service is living the dream and hopefully doing well"


# Model Upload endpoint expects a smpl model in .pkl format
# as also required by TEACH, TEMOS and other SMPL based models
# Example:
# curl -X POST "http://localhost:8000/upload_model/" \
# -F "model=@SMPL_NEUTRAL.pkl"
@app.post("/upload_model/", response_model=uuid.UUID)
async def upload_model(model: UploadFile) -> uuid.UUID:
    model_id = uuid.uuid4()
    processed = mh.store_model(model, model_id)
    if not processed:
        raise HTTPException(status_code=500, detail="Failed to store model")
    return model_id


# Generation endpoint, starts the generation processs in the background
# Example:
# curl "http://localhost:8000/generate/?motion_description=some_description&model_id=some_model_id&durations[]=1.0&durations[]=2.0"
@app.get("/generate/", response_model=uuid.UUID)
async def generate(motion_description: str, model_id: Optional[str] = None, durs: Optional[str] = Query(None)) -> uuid.UUID:
    request_id = uuid.uuid4()
    status_store[request_id] = dlhm_types.RequestStatus.REQUEST_RECEIVED
    if (model_id is not None) and (not mh.check_model_storage(model_id=uuid.UUID(model_id))):
        raise HTTPException(status_code=400, detail="Bad model_id")
    if durs is not None:
        durations = [float(x) for x in durs.split(",")]
    else:
        durations = []
    asyncio.create_task(
        mh.generate(
            motion_desc=motion_description,
            request_id=request_id,
            status_store=status_store,
            model_id=(model_id if model_id is not None else None),
            durations=(durations if durations is not None else []),
        )
    )

    return request_id


# Status endpoint, returns the status of a request
# Example:
# curl "http://localhost:8000/status/some_request_id"
# Possible statuses are defined in dlhm_types.RequestStatus
@app.get("/status/{request_id}", response_model=dlhm_types.RequestStatus)
async def get_status(request_id: uuid.UUID) -> dlhm_types.RequestStatus:
    if request_id not in status_store:
        raise HTTPException(status_code=404, detail="Request not found")
    return status_store[request_id]


# Download endpoint, returns a zip file with the generated motion data
# Example:
# curl -O "http://localhost:8000/download/some_request_id"
@app.get("/download/{request_id}", response_class=FileResponse)
async def download(request_id: uuid.UUID):
    if request_id not in status_store:
        raise HTTPException(status_code=404, detail="Request not found")

    status = status_store[request_id]
    if status != dlhm_types.RequestStatus.SUCCESS:
        raise HTTPException(status_code=425, detail="Request is not ready yet")

    folder_path = os.path.join(DEFAULT_OUTPUT_DIR, str(request_id))

    # Make a temp zip
    tmp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    base_name = tmp_zip.name.replace(".zip", "")

    shutil.make_archive(
        base_name=base_name,
        format="zip",
        root_dir=os.path.dirname(folder_path),
        base_dir=os.path.basename(folder_path),
    )

    return FileResponse(
        path=tmp_zip.name,
        filename=f"{request_id}.zip",
        media_type="application/zip",
    )
