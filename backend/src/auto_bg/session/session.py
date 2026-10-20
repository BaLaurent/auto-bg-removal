from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(frozen=True)
class ImageMeta:
    width: int
    height: int


@dataclass
class Session:
    id: str
    image_meta: ImageMeta
    model_name: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def new(cls, image_meta: ImageMeta, model_name: str) -> "Session":
        return cls(id=str(uuid4()), image_meta=image_meta, model_name=model_name)
