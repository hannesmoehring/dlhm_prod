import asyncio
import os
import subprocess
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


@app.get("/alive")
async def alive() -> str:
    return "Service is living the dream and hopefully doing well"


@app.post("/upload_model/", response_model=uuid.UUID)
async def upload_model(model: UploadFile) -> uuid.UUID:
    model_id = uuid.uuid4()
    processed = mh.store_model(model, model_id)
    if not processed:
        raise HTTPException(status_code=500, detail="Failed to store model")
    return model_id


@app.get("/generate/", response_model=uuid.UUID)
async def generate(motion_description: str, model_id: Optional[str] = None, durations: Optional[list[float]] = Query(default=None)) -> uuid.UUID:
    request_id = uuid.uuid4()
    status_store[request_id] = dlhm_types.RequestStatus.REQUEST_RECEIVED
    if (model_id is not None) and (not mh.check_model_storage(model_id=uuid.UUID(model_id))):
        raise HTTPException(status_code=400, detail="Bad model_id")

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


@app.get("/status/{request_id}", response_model=dlhm_types.RequestStatus)
async def get_status(request_id: uuid.UUID) -> dlhm_types.RequestStatus:
    if request_id not in status_store:
        raise HTTPException(status_code=404, detail="Request not found")
    return status_store[request_id]


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

    # This zips the folder itself, not just its contents
    shutil.make_archive(
        base_name=base_name,
        format="zip",
        root_dir=os.path.dirname(folder_path),  # parent directory
        base_dir=os.path.basename(folder_path),  # folder itself
    )

    return FileResponse(
        path=tmp_zip.name,
        filename=f"{request_id}.zip",
        media_type="application/zip",
    )
