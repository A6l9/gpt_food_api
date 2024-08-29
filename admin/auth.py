import base64
import hashlib
import hmac
import time
from typing import Optional

from asyncpg import ConnectionDoesNotExistError
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse

from config.config import SECRET_KEY
# from database.db_interface import BaseInterface
from database.initial import db


def generate_token(user_id: int) -> str:
    timestamp = str(int(time.time()))
    message = f"{user_id}:{timestamp}"
    signature = hmac.new(SECRET_KEY.encode(), message.encode(), hashlib.sha256).digest()
    token = base64.urlsafe_b64encode(f"{message}:{signature.hex()}".encode()).decode()
    return token


def decode_token(token: str, max_age: int = 3600) -> Optional[int]:
    """Возвращает id юзера или None если токен не валидный или просрочен"""
    try:
        decoded_token = base64.urlsafe_b64decode(token).decode()
        message, signature = decoded_token.rsplit(":", 1)
        user_id, timestamp = message.split(":")
        if int(time.time()) - int(timestamp) > max_age:
            return None
        expected_signature = hmac.new(SECRET_KEY.encode(), message.encode(), hashlib.sha256).digest()
        if hmac.compare_digest(expected_signature.hex(), signature):
            return int(user_id)
        return None
    except Exception:
        return None


class AdminAuth(AuthenticationBackend):
    """Отвечает за вход в админку. Сам создает страинцы авторизации"""

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get('username')
        password = form.get('password')
        # db_con = db
        try:
            user = await db.get_user_by_log_pas(login=username, password=password)
            if user is None:
                return False
        except ConnectionDoesNotExistError:
            return await self.login(request=request)

        request.session.update({"token": generate_token(user.id)})
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if request.url.path == '/admin/':
            return RedirectResponse('/admin')
        try:
            if not token:
                return False
            user_id = decode_token(token)
            if user_id is None:
                return False
            user = await db.get_user_bu_id(user_id=user_id)
            if user is None:
                return False
            return True
        except ConnectionDoesNotExistError:
            return await self.authenticate(request=request)
            # return False
