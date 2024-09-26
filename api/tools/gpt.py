import json
import pprint
import re
from io import BytesIO

from openai import AsyncClient
import asyncio
import base64

from database.initial import db
from api.tools.formatters import get_timezone_difference
from log_decor import *
from config.config import DATE_FORMAT


GPT_TOKEN = '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'
PROMT = (
    'Определи есть ли тут какое либо блюдо/еда/напиток. Если да то напиши ответ в формате: название всех блюд на фото с заглавной буквы через запятую и затем в скобках каждый продукт который ты увидел''Определи суммарно во всех продуктах питания на фото:'
    'Калории: int'
    'Белки: float г (int%)'
    'Жиры: float г (int%)'
    'Углеводы: float г (int%) – float ХЕ'
    'Общий вес: int г.'
    'Гликемический индекс: float г (int%)'
    'Если в продукте есть белки и жиры, то напиши: Внимание! Продукт содержит белково-жировые единицы (БЖЕ). В зависимости от общего количества жирной пищи может потребоваться дополнительно компенсировать БЖУ через 2-3 часа!'
    'Посчитай белково-жировые единицы: float г (int%) – float БЖЕ'
    'После напиши сообщение: Приятного аппетита!'
)

class GPT:
    time_pattern = r'\b(\d{2}-\d{2}-\d{4} \d{2}:\d{1,2})\b'

    def __init__(self, token: str, promt: str):
        self.promt = promt
        self.token = token
        self.client = AsyncClient(
            api_key=self.token
        )

    async def get_time_format(self, user_time):
        content = [
            {
                "role": "system",
                "content": f"Приведи дату к формату {DATE_FORMAT}"
            },
            {
                "role": "user",
                "content": user_time
            },
        ]
        for _ in range(5):
            stream = await self.client.chat.completions.create(
                model='gpt-4o-mini',
                messages=content
            )

            response = ''
            for choice in stream.choices:
                response += choice.message.content
            matches = re.findall(self.time_pattern, response)
            if matches:
                user_time_format = matches[0]
                time_diff = get_timezone_difference(user_time_format)
                return time_diff




    async def request(self, image: BytesIO):
        # with open(PROMPT_PATH) as f:
        #     text_prompt = f.read()
        image_base64 = base64.b64encode(image.getvalue()).decode('utf-8')
        while True:
            stream = await self.client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"{self.promt}"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ]

            )
            response = ''
            for choice in stream.choices:
                response += choice.message.content
            return response

    async def sub_request(self, message, db_con: db, user_id: int, user_date):

        content = [
        {
            "role": "system",
            "content": "You are a helpful assistant. Please format the response in the following JSON template."
        },
            {
                "role": "user",
                "content": message
            },
        {
            "role": "user",
            "content": """
                Please extract the relevant data from the text and format it in this JSON structure:
                
                {
                    "dish_name": <value>,
                    "calories": <value>,
                    "proteins": <value>.0,
                    "proteins_percent": <value>,
                    "fats": <value>,
                    "fats_percent": <value>,
                    "carbohydrates": <value>,
                    "carbohydrates_percent": <value>,
                    "bread_units": <value>,
                    "total_weight": <value>,
                    "glycemic_index": <value>,
                    "protein_bje": <value>,
                    "fats_bje": <value>,
                    "calories_bje": <value>,
                    "bje_units": <value>
                }
            """
        }
    ]

        response_json = None
        for _ in range(5):
            stream = await self.client.chat.completions.create(
                model='gpt-4o-mini',
                messages=content
            )

            response = ''
            for choice in stream.choices:
                response += choice.message.content
            try:
                json_pattern = re.compile(r'\{(?:[^{}]|(?R))*\}')
            except:
                json_pattern = re.compile(r'```json\s*({.*?})\s*```', re.DOTALL)

            # Find JSON-like text
            match = json_pattern.search(response)
            if match:
                try:
                    json_text = match.group(1)
                except:
                    json_text = match.group(0)
                try:
                    # Attempt to parse the JSON
                    response_json = json.loads(json_text)
                    break
                except json.JSONDecodeError:
                    # Handle error if the extracted text is not valid JSON
                    try:
                        response_json = json.loads(response)
                        break
                    except:
                        logger.info("Extracted text is not valid JSON: " + json_text)
            else:
                try:
                    response_json = json.loads(response)
                    break
                except:
                    # Handle case where no JSON was found
                    logger.info("No JSON found in the response: " + response)
        if response_json:
            response_json = {key: str(val) if val is not None else val for key, val in response_json.items()}
            await db_con.add_user_diarys(user_id, user_date, response_json)
            # return response

def gpt_check_request(text: str) -> bool:
    if text.lower().find('ошибка') == -1:
        return False
    return True


if __name__ == "__main__":
    pp = pprint.PrettyPrinter(indent=4)
    with open('../rulet.jpg', 'rb') as file:
        image_io = BytesIO(file.read())
    gpt = GPT()
    res = asyncio.run(gpt.request(image_io))
    print(res)
    data = asyncio.run(gpt.sub_request(res))

    print()
    pp.pprint(data)
