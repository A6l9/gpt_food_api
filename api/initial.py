from fastapi import FastAPI, APIRouter

api_app = FastAPI(
    # tags=['ShugarPulse API'],
    title='ShugarPulse API',
    # lifespan=lifespan
)
api_router = APIRouter()


