from datetime import datetime
from io import BytesIO

from fastapi import HTTPException, UploadFile, File
from fastapi.params import Query
from loguru import logger
from starlette.requests import Request
from starlette.responses import JSONResponse

from api.initial import api_router
from api.models.request_models.models import DiaryRequest, TextRequest
from api.models.response_models.models import FAQResponse, DiaryResponse, TextResponse
from api.tools.authentication import check_auth_hash, auth_process, check_widget_auth_hash, get_user_id_param
from api.tools.check_enable_requests import check_enable_requests
from api.tools.gpt import GPT, gpt_check_request
from api.tools.formatters import reformat_date
from database.initial import db, dbconf
from database.models import User, FoodDiary, UserRequest


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
            filter_by={'tg_user_id': str(auth_data['id'])},
            last_name=auth_data.get('last_name'),
            first_name=auth_data.get('first_name'),
            tg_user_id=str(auth_data['id']),
            tg_username=auth_data.get('username'),
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
        'list_all_dates': list_all_dates
    }
    if response_data:
        return response_data


@api_router.post('/get_user_photo', response_model=TextResponse)
async def get_user_photo(
        tg_user_id=get_user_id_param(),
        image: UploadFile=File(...),
        write_diary: str=None   #TextRequest
):
    user = await db.get_user_by_tg_id(tg_id=str(tg_user_id))
    if user is None:
        raise HTTPException(status_code=404, detail='User not found')
    if not await check_enable_requests(user, dbconf):
        raise HTTPException(status_code=403, detail='Error subscription ended.')
    if write_diary:
        if user.timezone is None:
            response_data = {
                'data': 'Чтобы вносить записи в дневник напишите вашу текущую дату и время в свободном формате'
            }
            return response_data
    image_bytes = await image.read()
    image_bufer = BytesIO(image_bytes)
    image_bufer.seek(0)
    try:
        gpt_token = (await dbconf.get_setting('gpt_token')).get_value()
        gpt_promt = (await dbconf.get_setting('gpt_promt')).get_value()
    except Exception as e:
        logger.error(e)
    logger.info(f'{gpt_token=}')
    logger.info(f'{gpt_promt=}')
    gpt = GPT(token=gpt_token, promt=gpt_promt)
    logger.info(f'{type(image_bytes)}')
    if write_diary:
        res = write_diary
        try:
            await gpt.sub_request(res, dbconf, user.id, reformat_date(datetime.utcnow(), user.timezone))
            response_data = {
                'data': 'Записано'
            }
            return response_data

        except HTTPException as exc:
            logger.error(exc)
            response_data = {
                'data': 'Ошибка записи'
            }
            return response_data
    else:
        try:
            user_requests = await db.get_row(UserRequest, user_id=user.id)
            for _ in range(3):
                if not (user_requests.subscribe_date_end and user_requests.subscribe_date_end > datetime.utcnow()):
                    res = await gpt.request(image_bufer)
                    if any(word in res for word in
                           ['Калории', 'Белки', 'Жиры', 'Углеводы', 'Хлебные единицы', 'ХЕ', 'Протеин']):
                        if gpt_check_request(res):
                            res = await gpt.request(image_bufer)
                        response_data = {
                            'data': res
                        }
                        return response_data
            else:
                response_data = {
                    'data': None
                }
                return response_data
        except HTTPException as exc:
            logger.error(exc)