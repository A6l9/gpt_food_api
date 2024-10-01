
from pydantic import BaseModel


class DiaryRequest(BaseModel):
    date: str | None = None

class TextRequest(BaseModel):
    # text: str | None = None
    timezone: str | None = None
    history_id: str | None = None

class PhotoRequest(BaseModel):
    image: str | None = None