import datetime
import os

from database.initial import db
from loguru import logger
import asyncio
from asyncio import Task
from database.models import TemporaryHistoryStorage


class Cleaner:
    db = db
    def __init__(self):
        self.task_storage: dict[int: Task] = {}
        self.history_list = []
        self.list_to_delete = []


    async def start(self):
        """
        Очищает папку с изображениями от неиспользуемых изображений
        :return:
        """
        logger.info('Start Cleaner')
        while True:
            self.history_list = await db.get_row(TemporaryHistoryStorage, order_by='datetime', to_many=True)
            for i_id in range(1):
                if self.task_storage.get(i_id):
                    cur_task = self.task_storage[i_id]
                    cur_task.cancel()
                    logger.info('Cur_task canceled')
                self.task_storage[i_id] = asyncio.create_task(self.clean_history())
                logger.info(f'create task{self.task_storage}')
            now = datetime.datetime.now(datetime.UTC)
            next_midnight = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            delta = next_midnight - now
            logger.debug(f"There are hours left until midnight: {round(delta.total_seconds() / 3600, 1)}")
            logger.debug(f"Going to sleep")
            await asyncio.sleep(delta.total_seconds())


    async def clean_history(self):
        """
        Очищает историю от старых записей
        :return:
        """
        logger.info('Start Cleaner History')
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        for history in self.history_list:
            logger.debug(history.datetime.strftime('%Y-%m-%d'))
            if history.datetime.strftime('%Y-%m-%d') != current_date:
                dir_path = '/'.join(os.path.abspath('api').split('/')[:-2]) + history.path_to_photo
                logger.debug(f"History is recorded: {history.recorded}")
                logger.debug(f"Abs path to photo: {dir_path}")
                logger.debug(f"Path is exists: {os.path.exists(dir_path)}")
                if os.path.exists(dir_path) and not history.recorded:
                    os.remove(dir_path)
                    logger.debug("Unused photo has been deleted")
                self.list_to_delete.append(history.id)
        await db.delete_old_records(self.list_to_delete)
        logger.info('End Cleaner History')


async def cleaner_history():
    x = Cleaner()
    await x.start()
