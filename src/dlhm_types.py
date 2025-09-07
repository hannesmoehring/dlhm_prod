from enum import Enum
from typing import Optional

from pydantic import BaseModel


class MotionDescription(BaseModel):
    text: str
    durs: Optional[list[int]]


class ModelInput(BaseModel):
    model: object


# Possible statuses for a request
class RequestStatus(Enum):
    FAILED = "Process failed."

    REQUEST_RECEIVED = "Request received."
    LOADED_MESH = "Mesh loaded."
    PREPARED_MESH = "Mesh prepared."
    GENERATION_STARTED = "Generation started."
    GENERATION_FINISHED = "Generation finished."
    SUCCESS = "Ready for download.  Download at /download/{request_id}."
