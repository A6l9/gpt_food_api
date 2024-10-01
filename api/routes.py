import base64
import datetime
from io import BytesIO
import asyncio
import os

from fastapi import HTTPException
from fastapi.params import Query
from loguru import logger
from sqlalchemy.orm import class_mapper
from starlette.requests import Request
from starlette.responses import JSONResponse

from api.initial import api_router
from api.models.request_models.models import DiaryRequest, TextRequest, PhotoRequest
from api.models.response_models.models import FAQResponse, DiaryResponse, TextResponse, TextResponseNoPhoto
from api.tools.authentication import check_auth_hash, auth_process, check_widget_auth_hash, get_user_id_param
from api.tools.check_enable_requests import check_enable_requests
from api.tools.gpt import GPT, gpt_check_request
from api.tools.formatters import reformat_date
from api.tools.task_storage import TaskStorage
from database.initial import db, dbconf
from database.models import User, FoodDiary, UserRequest, TemporaryHistoryStorage


@api_router.get('/faq', response_model=FAQResponse)
async def get_faq(
        search = Query(None)
):
    result = await db.get_faq(search)
    return JSONResponse(content={'data': result}, status_code=200)


@api_router.post('/auth')
async def auth_router(
        request: Request,
):
    auth_data = await request.json()
    logger.info(f'{auth_data=}')
    if auth_data.get('user'):
        check_auth_hash(auth_data)
        user_id = await db.get_row(User.id, tg_id=str(auth_data['user']['id']))
        if user_id:
            return await auth_process(user_id, auth_data)
    else:
        check_widget_auth_hash(auth_data)
        logger.info('Success check hash')
        user = await db.get_or_create_user(
            filter_by={'tg_id': str(auth_data['id'])},
            tg_id=str(auth_data['id']),
            username=auth_data.get('username'),
        )
        return await auth_process(user.id, auth_data)
    raise HTTPException(status_code=403)


@api_router.post('/diaries', response_model=DiaryResponse)
async def get_diaries(
        user_id=get_user_id_param(),
        request: DiaryRequest=None
) -> dict:
    diaries_on_request = []
    list_all_dates = []
    if request.date:
        data_diary = await db.get_row(FoodDiary, user_id=int(user_id), to_many=True)
        diaries_on_request = [i.get_data()
                   for i in data_diary if str(i.get_data().get('updated_at_without_time')) == request.date]
        more_diaries = [i.get_data().get('updated_at_without_time')
                   for i in data_diary if str(i.get_data().get('updated_at_without_time')) != request.date]
        if more_diaries:
            list_all_dates = list(dict.fromkeys(more_diaries))
    response_data = {
        'data': diaries_on_request,
        'list_all_dates': list_all_dates,
    }
    if response_data:
        return response_data


@api_router.post('/check_food', response_model=TextResponseNoPhoto)
async def check_food_endpoint(
        image: PhotoRequest,
        user_id=get_user_id_param()
):
    list_available_types = ['png', 'jpeg', 'gif', 'webp', 'jpg']
    image_str = image.image.split(',')
    if any(word in image_str[0] for word in
           list_available_types):
        image_str = image_str[1]
    else:
        response_data = {
            'data': 'Невалидный формат изображения'
        }
        return response_data
    byte_data = base64.b64decode(image_str)
    task_storage = TaskStorage.task_storage
    if task_storage.get(int(user_id)):
        cur_task = task_storage[int(user_id)]
        cur_task.cancel()
    task_storage[int(user_id)] = asyncio.create_task(check_food_func(user_id, byte_data))
    response_data = {
        'data': str(user_id)
    }
    return response_data


async def check_food_func(user_id, image):
    user = await db.get_row(User, id=int(user_id))
    user_requests = await db.get_row(UserRequest, user_id=user.id)
    if not (user_requests.subscribe_date_end
            and user_requests.subscribe_date_end > datetime.datetime.utcnow() or user.is_admin):
        response_data = {
            'data': 'Закончилась подписка',
            'path_to_photo': None,
            'write_in_diary': False,
            'history_id': None
        }
        return response_data
    if user is None:
        raise HTTPException(status_code=404, detail='User not found')
    if not await check_enable_requests(user, dbconf):
        raise HTTPException(status_code=403, detail='Error subscription ended.')
    date = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d")
    dir_path = os.path.exists(f'./api/static/images/{date}')
    if not dir_path:
        os.mkdir(f'./api/static/images/{date}')
    if not os.path.exists(f'./api/static/images/{date}/{user_id}'):
        os.mkdir(f'./api/static/images/{date}/{user_id}')
    dir_path = os.path.abspath(f'./api/static/images/{date}/{user_id}')
    image_bufer = BytesIO(image)
    image_bufer.seek(0)
    try:
        gpt_token = (await dbconf.get_setting('gpt_token')).get_value()
        gpt_promt = (await dbconf.get_setting('gpt_promt')).get_value()
    except Exception as e:
        logger.error(e)
    logger.info(f'{gpt_token=}')
    logger.info(f'{gpt_promt=}')
    gpt = GPT(token=gpt_token, promt=gpt_promt)
    try:
        res = await gpt.request(image_bufer)
        for _ in range(3):
            if any(word in res for word in
                   ['Калории', 'Белки', 'Жиры', 'Углеводы', 'Хлебные единицы', 'ХЕ', 'Протеин']):
                if gpt_check_request(res):
                    res = await gpt.request(image_bufer)
                time_now = datetime.datetime.strftime(datetime.datetime.now(datetime.UTC), '%I:%M:%S')
                with open(f'{dir_path}/{time_now}.jpg', 'wb') as new_file:
                    new_file.write(image)
                dir_path = f'/static/images/{date}/{user_id}/{time_now}.jpg'
                result = await db.add_row(TemporaryHistoryStorage, user_id=int(user_id), path_to_photo=dir_path,
                                 text=res, recorded=False, datetime=datetime.datetime.utcnow().replace(microsecond=0))
                response_data = {
                    'data': res.replace('\n', '<br />'),
                    'path_to_photo': dir_path,
                    'write_in_diary': True,
                    'history_id': str(result.id)

                }
                return response_data
        else:
            response_data = {
                'data': res,
                'path_to_photo': None,
                'write_in_diary': False,
                'history_id': None

            }
            return response_data


    except HTTPException as exc:
        logger.error(exc)


@api_router.get('/check_ready', response_model=TextResponse)
async def check_ready_or_not(
        user_id=get_user_id_param()
):
    try:
        task_storage = TaskStorage.task_storage
        if task_storage.get(int(user_id)):
            if task_storage[int(user_id)].done():
                logger.info('Task has been completed')
                result = task_storage[int(user_id)].result()
                response_data = {
                    'data': result.get('data', ''),
                    'path_to_photo': result.get('path_to_photo'),
                    'write_in_diary': result.get('write_in_diary'),
                    'history_id': result.get('history_id')
                }
                logger.debug('Ответ готов')
                cur_task = task_storage.pop(int(user_id), None)
                logger.debug('Task has been deleted')
                logger.debug(f'Task storage: {task_storage}')
                return response_data
        logger.debug('Task storage is empty')
        response_data = {
            'data': '',
            'path_to_photo': None,
            'write_in_diary': None,
            'history_id': None
        }
        return response_data
    except Exception as exc:
        logger.exception(f'Exception: {exc}')
        response_data = {
            'data': '',
            'path_to_photo': None,
            'write_in_diary': None,
            'history_id': None
        }
        return response_data


@api_router.post('/save_diary', response_model=TextResponseNoPhoto)
async def save_diary(
        request: TextRequest,
        user_id=get_user_id_param()
):
    user = await db.get_row(User, id=int(user_id))
    temp = await db.get_row(TemporaryHistoryStorage, id=int(request.history_id))
    if user is None:
        raise HTTPException(status_code=404, detail='User not found')
    if not await check_enable_requests(user, dbconf):
        raise HTTPException(status_code=403, detail='Error subscription ended.')
    if user.timezone is None:
        await db.update_timediff(int(user_id), int(request.timezone))
    gpt_token = (await dbconf.get_setting('gpt_token')).get_value()
    gpt_promt = (await dbconf.get_setting('gpt_promt')).get_value()
    gpt = GPT(token=gpt_token, promt=gpt_promt)
    asyncio.create_task(
        gpt.sub_request(temp.text, db, user.id,
                        reformat_date(datetime.datetime.utcnow(), int(request.timezone)), path_to_photo=temp.path_to_photo)
    )
    response_data = {
        'data': 'Записано'
    }
    await db.update_status(his_id=int(request.history_id), status=True)
    return response_data
