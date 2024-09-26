import hashlib
import hmac
import json
from datetime import datetime

from fastapi import Depends, Query, Body
from fastapi.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from api.models.request_models.auth_model import AuthRequest
from api.tools.jwt_gen import JWTGenerate
from config.config import AUTH_BY_TOKEN, APP_BOT_TOKEN


async def auth_process(user_id, auth_data):
    response = JSONResponse(content={'status': 'success'}, status_code=200)
    auth_date = round(datetime.utcnow().timestamp())
    auth = AuthRequest(
        user_id=user_id,
        tg_user_id=auth_data['user']['id'] if auth_data.get('user') else auth_data['id'],
        auth_date=auth_date
    )
    user_data = auth_data['user'] if auth_data.get('user') else auth_data
    user_data.pop('auth_date', None)
    data = {
        'session_id': await AuthRequest.get_user_hash(auth),
        'auth_date': str(auth_date),
        **user_data
    }
    token = await JWTGenerate.generate_jwt(data)
    response.headers['Authorization'] = f'Bearer {token}'
    return response


def get_user_id_param(default=..., include_in_schema=True, field_type='body'):
    if AUTH_BY_TOKEN:
        return Depends(get_user_id)
    else:
        if field_type == 'query':
            return Query(default, description='User ID', include_in_schema=include_in_schema)
        elif field_type == 'body':
            return Body(default, description='User ID', include_in_schema=include_in_schema)


async def get_user_id(request: Request):
    headers = request.headers
    user_token = headers.get('Authorization')
    if not user_token or user_token == 'null':
        raise HTTPException(status_code=403)
    user_data = await JWTGenerate.decode_jwt(user_token.split(' ')[-1])
    auth = AuthRequest(
        tg_user_id=user_data.get('id'),
        auth_date=user_data.get('auth_date'),
        session_id=user_data.get('session_id'),
    )
    return await auth.check_auth()


def encode_value(value):
    """ Кодирует значение в строку, если это словарь, то сериализует его в JSON. """
    if isinstance(value, dict):
        return json.dumps(value, separators=(',', ':'), ensure_ascii=False)
    return str(value)


def create_body(data):
    """ Формирует тело запроса в формате 'key=value' с учетом всех инструкций. """
    sorted_items = sorted((k, encode_value(v)) for k, v in data.items() if k != "hash")
    body = "\n".join(f"{k}={v}" for k, v in sorted_items)
    return body


def check_auth_hash(auth_data):
    hash_value = auth_data.pop("hash", None)
    body = create_body(auth_data)
    secret_key = hmac.new(b'WebAppData', APP_BOT_TOKEN.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, body.encode(), hashlib.sha256).hexdigest()
    if computed_hash == hash_value:
        print("Hashes match!")
    else:
        print("Hashes do not match!")
        raise HTTPException(status_code=403)


def check_widget_auth_hash(auth_data):
    check_hash = auth_data.pop('hash')
    data_check_arr = [f"{key}={value}" for key, value in auth_data.items()]
    data_check_arr.sort()
    data_check_string = "\n".join(data_check_arr)
    secret_key = hashlib.sha256(APP_BOT_TOKEN.encode()).digest()
    hash_value = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if hash_value != check_hash:
        raise HTTPException(status_code=403)


if __name__ == '__main__':
    auth_data = {
    "id": 793160420,
    "first_name": "Арина",
    "last_name": "Ефимова",
    "username": "arrra_efimova",
    "auth_date": "1727350707",
    "hash": "50a5ff84fdc2d47bb349c925334d7710a36c21b2209339f4ab69243e1417bfdd"
}
    check_auth_hash(auth_data)

