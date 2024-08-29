from fastapi.params import Query
from starlette.responses import RedirectResponse, JSONResponse

from api.initial import api_app, api_router
from api.models.response_models.models import FAQResponse
from database.initial import db


@api_router.get('/faq', response_model=FAQResponse)
async def get_faq(
        search = Query(None)
):
    result = await db.get_faq(search)
    return JSONResponse(content={'data': result}, status_code=200)
