from pydantic import BaseModel


class FAQResponse(BaseModel):
    class Item(BaseModel):
        question: str
        answer: str
    data: list[Item]