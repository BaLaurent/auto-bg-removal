from typing import Literal

from pydantic import BaseModel, Field


class ImageSize(BaseModel):
    width: int
    height: int


class SessionCreated(BaseModel):
    session_id: str
    image: ImageSize
    embedding_ready: bool
    model: str


class SessionState(BaseModel):
    session_id: str
    embedding_ready: bool
    model: str


class PointDTO(BaseModel):
    x: int
    y: int
    label: Literal[0, 1] = 1


class BoxDTO(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int


class PredictRequest(BaseModel):
    mode: Literal["points", "box", "auto"]
    points: list[PointDTO] | None = None
    box: BoxDTO | None = None


class MaskRLEDTO(BaseModel):
    counts: str = Field(description="base64-encoded COCO RLE counts")
    size: tuple[int, int] = Field(description="[height, width]")


class PredictResponse(BaseModel):
    mask: MaskRLEDTO
    score: float
    model: str


class ModelInfo(BaseModel):
    name: str
    loaded: bool
    size_mb: int | None = None


class ModelsResponse(BaseModel):
    active: str
    available: list[ModelInfo]


class SetActiveRequest(BaseModel):
    name: str


class ExportRequest(BaseModel):
    mask: MaskRLEDTO
