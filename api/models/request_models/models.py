
from pydantic import BaseModel


class DiaryRequest(BaseModel):
    date: str | None = None

class ImageRequest(BaseModel):
    image: bytes