from pydantic import BaseModel


class MotionDescription(BaseModel):
    data: list[tuple[str, float]]


class ModelInput(BaseModel):
    # TODO: Define for smpl inputs
    model: object
