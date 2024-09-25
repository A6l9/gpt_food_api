from abc import ABC

import jwt
from fastapi import HTTPException

from config.config import JWT_ALGORITHM, HASH_SECRET_KEY
from log_decor import *


@loguru_decorate
class JWTGenerate(ABC):

    @classmethod
    async def generate_jwt(cls, data: dict):
        return jwt.encode(data, HASH_SECRET_KEY, algorithm=JWT_ALGORITHM)

    @classmethod
    async def decode_jwt(cls, token):
        try:
            return jwt.decode(token, HASH_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        except Exception as e:
            logger.exception(e)
            raise HTTPException(status_code=403)
