from datetime import datetime, timedelta

from database.initial import db
from database.models import User, UserRequest
from api.tools.formatters import get_next_monday


async def check_enable_requests(user: User, db: db, add=True):
    if user.is_admin:
        return True
    user_requests = await db.get_or_create_row(
        UserRequest,
        filter_by={'user_id': user.id},
        user_id=user.id,
        next_upd_free=get_next_monday()
    )

    if user_requests.subscribe_date_end and user_requests.subscribe_date_end > datetime.utcnow():
        return True

    free_requests_days = (await db.get_setting('free_requests')).get_value()
    dead_line = user.created_at + timedelta(days=int(free_requests_days))
    diff_datetime = dead_line - datetime.utcnow()
    if diff_datetime.total_seconds() > 0:
        # if add:
        #     await db.update_row(
        #         UserRequest,
        #         filter_by={'user_id': user.id},
        #         usage_free_requests=user_requests.usage_free_requests + 1
        #     )
        return True
    # elif user_requests.next_upd_free < datetime.utcnow():
    #     await db.update_row(
    #         UserRequest,
    #         filter_by={'user_id': user.id},
    #         next_upd_free=user_requests.next_upd_free + timedelta(days=7),
    #         usage_free_requests=1
    #     )
    #     return True
    return False
