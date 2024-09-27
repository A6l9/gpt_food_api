import hashlib

from fastapi import HTTPException
from pydantic import BaseModel

from config.config import HASH_SECRET_KEY
from database.models import User
from database.initial import db


class AuthRequest(BaseModel):
    tg_user_id: str | int | None = None
    user_id: str | int | None = None
    auth_date: int | None = None
    session_id: str | None = None

    # @classmethod
    async def check_auth(self):
        self.user_id = await db.get_row(User.id, tg_id=str(self.tg_user_id))
        if self.user_id:
            user_hash = await self.get_user_hash(self)
            if user_hash == self.session_id:
                return self.user_id
        raise HTTPException(status_code=403)

    @classmethod
    async def get_user_hash(cls, self):
        raw_str = f'{self.tg_user_id}{self.user_id}{self.auth_date}{HASH_SECRET_KEY}'
        return hashlib.md5(raw_str.encode()).hexdigest()

