from pydantic import BaseModel


class DiaryRequest(BaseModel):
    date: str | None = None
