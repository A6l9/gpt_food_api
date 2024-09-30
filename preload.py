from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from admin.initial import admin_app, admin_router
from api.initial import api_app, api_router

root_app = FastAPI(
    # lifespan=lifespan
)
root_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Authorization"]
)

root_app.mount('/admin', admin_app)
root_app.mount('/api', api_app)
# admin_app.mount("/statics", StaticFiles(directory="./sqladmin/statics"), name="statics")
api_app.include_router(api_router, tags=['Routes'])
admin_app.include_router(admin_router, tags=['Routes'])
api_app.mount("/static", StaticFiles(directory="./api/static"), name="static")
