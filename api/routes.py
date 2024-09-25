
from fastapi import HTTPException
from fastapi.params import Query
from loguru import logger
from starlette.requests import Request
from starlette.responses import JSONResponse

from api.initial import api_router
from api.models.request_models.models import DiaryRequest
from api.models.response_models.models import FAQResponse, DiaryResponse
from api.tools.authentication import check_auth_hash, auth_process, check_widget_auth_hash, get_user_id_param
from database.initial import db
from database.models import User, FoodDiary


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
        user_id = await db.get_row(User.id, tg_user_id=str(auth_data['user']['id']))
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
