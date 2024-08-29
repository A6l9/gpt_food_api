from fastapi import FastAPI, APIRouter
from sqladmin import Admin

from admin.auth import AdminAuth
from admin.views import FAQView
from database.initial import db

admin_app = FastAPI(
    tags=['Admin'], include_in_schema=False
    # lifespan=lifespan
)
admin_router = APIRouter()
authentication_backend = AdminAuth(secret_key="123")
admin = Admin(admin_app, engine=db.engine, session_maker=db.async_ses, authentication_backend=authentication_backend, base_url='/admin')
admin.add_view(FAQView)

# include_routes(app)
