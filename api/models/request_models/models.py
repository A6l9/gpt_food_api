
from pydantic import BaseModel


class DiaryRequest(BaseModel):
    date: str | None = None

class TextRequest(BaseModel):
    write_diary: str | None = None