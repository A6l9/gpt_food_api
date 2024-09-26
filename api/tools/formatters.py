import re
from datetime import datetime, timedelta

from config.config import DATE_FORMAT

translate = {
  "dish_name": "Название блюда",
  "calories": "Калории",
  "proteins": "Белки",
  "proteins_percent": "Белки_процент",
  "fats": "Жиры",
  "fats_percent": "Жиры_процент",
  "carbohydrates": "Углеводы",
  "carbohydrates_percent": "Углеводы_процент",
  "bread_units": "Хлебные единицы",
  "total_weight": "Общий вес",
  "glycemic_index": "Гликемический индекс",
  "protein_bje": "Протеин",
  "fats_bje": "Жиры (БЖЕ)",
  "calories_bje": "Калории (БЖЕ)",
  "bje_units": "БЖЕ"
}

class CustomCall:
    def __init__(self, message):
        self.message = message
        self.data = ''

def deadline_formatter(td):

    # Получаем все части временного интервала
    total_seconds = int(td.total_seconds())

    days = total_seconds // (24 * 3600)
    total_seconds %= (24 * 3600)

    hours = total_seconds // 3600
    total_seconds %= 3600

    minutes = total_seconds // 60
    # seconds = total_seconds % 60
    text = ''

    text += f'Дней: {days}\n'
    text += f'Часов: {hours}\n'
    text += f'Минут: {minutes}\n'

    return text


def get_next_monday():
    today = datetime.now()  # Получаем текущий объект datetime
    days_ahead = 7 - today.weekday()  # Вычисляем сколько дней до ближайшего понедельника
    if days_ahead == 7:  # Если сегодня понедельник, то вернем следующий понедельник
        days_ahead = 0
    next_monday = today + timedelta(days=days_ahead)

    # Установим время на начало дня (00:00:00)
    next_monday = next_monday.replace(hour=0, minute=0, second=0, microsecond=0)

    return next_monday


def get_timezone_difference(target_datetime_str):
    # Получение текущего времени на сервере
    server_datetime = datetime.utcnow()

    # Преобразование строки с целевым временем в объект datetime
    target_datetime = datetime.strptime(target_datetime_str, DATE_FORMAT).replace(year=server_datetime.year)

    # Вычисление разницы между двумя временными метками
    time_difference = server_datetime - target_datetime

    # Получение разницы в часах, округление до целого числа
    timezone_offset = round(time_difference.total_seconds() / 3600) * -1

    return timezone_offset


def reformat_date(date: datetime, time_diff):
    # date = date.replace(year=2024)
    if time_diff > 0:
        new_date = date + timedelta(hours=time_diff)
    elif time_diff < 0:
        new_date = date - timedelta(hours=abs(time_diff))
    else:
        new_date = date
    new_date = datetime.utcnow().replace(
        year=new_date.year,
        month=new_date.month,
        day=new_date.day,
        hour=new_date.hour,
        minute=new_date.minute,
        second=new_date.second,
        microsecond=0
    )
    return new_date


def format_text(text: str, format_dict: dict) -> str:
    """Преобразует текст подставляя в него ппеременные
    Просто format не работает из-за пробелов"""
    clean_text = re.sub(r'{{\s+', '{', text)
    clean_text = re.sub(r'\s+}}', '}', clean_text)

    matches = re.findall(r"\{(\w+)\}", clean_text)
    result = {match: '' for match in matches}
    result.update(format_dict)

    return clean_text.format(**result)


if __name__ == '__main__':
    print(('-3').isdigit())