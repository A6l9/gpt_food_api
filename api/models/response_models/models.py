from pydantic import BaseModel


class FAQResponse(BaseModel):
    class Item(BaseModel):
        question: str
        answer: str
    data: list[Item]

class DiaryResponse(BaseModel):
    class Item(BaseModel):
        dish_name: str | None
        calories: str | None
        proteins: str | None
        fats: str | None
        fats_percent: str | None
        carbohydrates: str | None
        carbohydrates_percent: str | None
        bread_units: str | None
        total_weight: str | None
        glycemic_index: str | None
        protein_bje: str | None
        fats_bje: str | None
        calories_bje: str | None
        bje_units: str | None
        path_to_photo: str | None
        updated_at: str | None
        updated_at_without_time: str | None
    data: list[Item | None]
    list_all_dates: list[str | None]


class TextResponse(BaseModel):
    data: str | None
    path_to_photo: str | None
    write_in_diary: bool | None
    history_id: str | None


class TextResponseNoPhoto(BaseModel):
    data: str | None


class HistoryResponse(BaseModel):
    class Item(BaseModel):
        text: str | None
        path_to_photo: str | None
        recorded: bool | None
        datetime: str | None
    data: list[Item | None]
