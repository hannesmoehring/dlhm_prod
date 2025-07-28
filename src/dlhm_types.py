from typing import Optional
from pydantic import BaseModel


class MotionDescription(BaseModel):
    text: str
    durs: Optional[list[int]]


class ModelInput(BaseModel):
    # TODO: Define for smpl inputs
    model: object
