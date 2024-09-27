
from pydantic import BaseModel


class DiaryRequest(BaseModel):
    date: str | None = None

class TextRequest(BaseModel):
    text: str | None = None
    timezone: str | None = None