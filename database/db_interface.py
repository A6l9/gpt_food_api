import asyncio
from datetime import datetime
from operator import or_
from typing import Any, Iterable, Optional, List

from sqlalchemy import Select, update, select, delete
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import Query
from sqlalchemy.sql.ddl import DropTable

from config.config import DB_URL
from database.models import Base, UserAuth, FAQ, User, Config, TypeEnum, FoodDiary, TemporaryHistoryStorage
from log_decor import *


@loguru_decorate
class BaseInterface:
    def __init__(self, db_url: str):
        """
        Класс-интерфейс для работы с БД. Держит сессию и предоставляет методы для работы с БД.

        :param db_url: Путь к БД формата: "database+driver://name:password@host/db_name"
        self.base базовый класс моделей с которыми будете работать.
        """
        self.engine = create_async_engine(db_url, pool_timeout=60, pool_size=900, max_overflow=100)
        self.async_ses = async_sessionmaker(bind=self.engine, class_=AsyncSession, expire_on_commit=False)
        self.base = Base

    async def initial(self):
        """
        Метод иницилизирует соеденение с БД.
        :return:
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(self.base.metadata.create_all)

    async def _drop_all(self):
        """
        Метод для удаления всех таблиц текущей БД.
        :return:
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(self.base.metadata.drop_all)

    async def del_has_rows(self, rows_object):
        async with self.async_ses() as session:
            for rec in rows_object:
                await session.delete(rec)
            # await session.delete(records)
            await session.commit()

    async def delete_rows(self, model: Any, **filter_by):
        async with self.async_ses() as session:
            records = await session.execute(Query(model).filter_by(**filter_by))
            res = records.scalars()
            if res:
                try:
                    for rec in res:
                        await session.delete(rec)
                    # await session.delete(records)
                    await session.commit()
                    return True
                except Exception:
                    pass

    async def get_all_set(self, table_model, field) -> set:
        """
        Метод принимает класс модели и название поля,
        и возвращает множество всех полученных значений.
        :param table_model: Класс модели
        :param field: Название поля
        :return: set
        """
        async with self.async_ses() as session:
            rows = await session.execute(Select(table_model.__table__.c[field]))
            return {row for row in rows.scalars()}

    async def drop_tables(self, table_models: Iterable):
        """
        Метод принимает коллекцию классов моделей и удаляет данные таблицы из БД.
        :param table_models:
        :return:
        """
        async with self.async_ses() as session:
            for table in table_models:
                await session.execute(DropTable(table.__table__))
                logger.info(f'{table.__tablename__} is dropped')
            await session.commit()

    async def add_row(self, model: Any, **kwargs):
        """
        Метод принимает класс модели и поля со значениями,
        и создает в таблице данной модели запись с переданными аргументами.
        :param model: Класс модели
        :param kwargs: Поля и их значения
        :return:
        """

        async with self.async_ses() as session:
            row = model(**kwargs)
            session.add(row)
            try:
                await session.commit()
                return row
            except Exception as ex:
                logger.warning(f'FAILED ADD ROW, {model.__name__}, {kwargs=}')
                return

    async def get_row(self, model: Any, to_many=False, order_by='id', filter=None, **kwargs):
        """
        Метод принимает класс модели и имена полей со значениями,
        и если такая строка есть в БД - возвращает ее.
        :param to_many: Флаг для возврата одного или нескольких значений
        :param model: Класс модели
        :param order_by:
        :param filter:
        :param kwargs: Поля и их значения
        :return:
        """
        async with self.async_ses() as session:
            # async with self.locks.get(model, asyncio.Lock()):
            if filter:
                row = await session.execute(
                    Query(model).filter_by(**kwargs).filter(filter['filter']).order_by(order_by))
            else:
                row = await session.execute(Query(model).filter_by(**kwargs).order_by(order_by))
            if to_many:
                res = [*row.scalars()]
            else:
                res = row.scalar()
            # if res is not None:
            return res

    async def get_or_create_row(self, model: Any, filter_by=None, **kwargs):
        """
        Метод находит в БД запись, и возвращает ее. Если записи нет - создает и возвращает.
        :param model: Класс модели
        :param filter_by: Параметры для поиска записи. По умолчанию поиск идет по **kwargs
        :param kwargs: Поля и их значения
        :return:
        """
        if not filter_by:
            filter_by = kwargs

        async with self.async_ses() as session:
            # async with self.locks.get(model, asyncio.Lock()):
            row = await session.execute(Query(model).filter_by(**filter_by))
            res = row.scalar()
            if res is None:
                res = model(**kwargs)
                session.add(res)
                try:
                    await session.commit()
                except Exception as ex:
                    logger.warning(f'COMMIT FAILED: {model.__name__}, {kwargs=}')
                    # print(ex)
            return res

    async def update_row(self, model, filter_by, **kwargs):

        async with self.async_ses() as session:
            # async with self.locks.get(model, asyncio.Lock()):
            row = await session.execute(update(model).filter_by(**filter_by).values(**kwargs))

            try:
                await session.commit()
                # return row.scalar()
            except Exception as ex:
                print(ex)
                print(f'failed update {model.__tablename__}')
                # raise HTTPException(status_code=500, detail='Ошибка обновления')

    async def update_timediff(self, user_id, timediff):
        async with self.async_ses() as session:
            await session.execute(
                update(User).filter_by(id=user_id).values(timezone=timediff)
            )
            await session.commit()

    async def update_status(self, his_id, status):
        async with self.async_ses() as session:
            try:
                await session.execute(
                    update(TemporaryHistoryStorage).filter_by(id=his_id).values(recorded=status)
                )
                await session.commit()
            except Exception as exc:
                logger.exception(exc)

    async def delete_old_records(self, lst_id: List):
        async with self.async_ses() as session:
            records = await session.execute(
                delete(TemporaryHistoryStorage)
                .filter(
                    TemporaryHistoryStorage.id.in_(lst_id)
                )
            )
            await session.commit()
            logger.info('Delete old records')

@loguru_decorate
class DBInterface(BaseInterface):
    def __init__(self, db_url: str):
        super().__init__(db_url)

    async def get_user_by_log_pas(self, login: str, password: str) -> Optional[UserAuth]:
        """Возвращает юзера. Пароль передается не хешированный"""
        async with self.async_ses() as session:
            row = await session.execute(Query(UserAuth).filter_by(username=login))
            # row = session.scalars(select(UserAuth).filter_by(username=login)).first()
            if row:
                row = row.scalar()
                if row.check_password(password=password):
                    return row
            return

    async def get_user_bu_id(self, user_id: int) -> Optional[UserAuth]:
        async with self.async_ses() as session:
            row = await session.execute(Query(UserAuth).filter_by(id=user_id))
            return row.scalar()

    async def get_user_by_tg_id(self, tg_id: str) -> Optional[User]:
        async with self.async_ses() as session:
            query = select(User).filter(User.tg_id == tg_id)
            result = (await session.scalars(query)).first()
        return result

    async def get_faq(self, search=None):
        if search:
            query = (
                Query(FAQ)
                .filter(
                    or_(
                        FAQ.question.ilike(f"%{search}%"),
                        FAQ.answer.ilike(f"%{search}%"),
                    )
                )
                .order_by('id')
            )
        else:
            query = Query(FAQ).order_by('id')
        async with self.async_ses() as session:
            rows = await session.execute(query)
            if rows:
                return [
                    row.get_data()
                    for row
                    in [*rows.scalars()]
                ]
            return []

    async def add_user_diarys(self, user_id, date_create, diary_data, path_to_photo=None):
        model = FoodDiary(
            user_id=user_id,
            created_at=date_create,
            updated_at=datetime.utcnow().replace(microsecond=0),
            path_to_photo=path_to_photo,
            **diary_data
        )
        async with self.async_ses() as session:
            session.add(model)
            try:
                await session.commit()
                logger.info(f'Diary for user: {user_id} added')
            except Exception as e:
                logger.exception(f'Failed add Diary for user: {user_id}: {e}')


class ConfigInterface(BaseInterface):

    async def get_setting(self, unique_name: str) -> Optional[Config]:
        """get_or_none Для поиска фраз по уникальному ключу. Возвращает сттроку, а не обьект таблицы"""
        async with self.async_ses() as session:
            row = await session.execute(Query(Config).filter_by(unique_name=unique_name))
            res = row.scalar()
            if res is None:
                return None
            return res


async def main():
    db = DBInterface(DB_URL)
    dbconf = ConfigInterface(DB_URL)
    await db.initial()
    model = UserAuth(
        username='admin',
        name='admin'
    )
    model.set_password('admin')
    async with db.async_ses() as session:
        session.add(model)
        await session.commit()
#     data = [
#     {
#         "question": "Нужно ли мне есть только «продукты для диабетиков»?",
#         "answer": "Нет, при соблюдении принципов здорового питания употребления специальных продуктов для пациентов с диабетом не требуется."
#     },
#     {
#         "question": "Что такое гликемический индекс продуктов?",
#         "answer": "Гликемический индекс - это условное обозначение скорости расщепления и всасывания любого продукта, содержащего углеводы, по сравнению со скоростью расщепления глюкозы. Гликемический индекс глюкозы составляет 100 единиц и принят за эталон. Чем быстрее происходит расщепление продукта — тем выше его гликемический индекс."
#     },
#     {
#         "question": "Зачем нужно знать гликемический индекс?",
#         "answer": "Углеводы в еде бывают простые и сложные. В организме усваивается только глюкоза и крахмалистые вещества, которые распадаются в процессе пищеварения на молекулы глюкозы. Инсулин нужен организму только для усвоения глюкозы, поэтому для людей с диабетом, при котором есть нехватка инсулина, в первую очередь важно содержание глюкозы в продуктах. Продукты с высоким гликемическим индексом практически полностью состоят из глюкозы или крахмала. Если гликемический индекс средний и высокий, для расчёта дозы инсулина достаточно посчитать количество продукта в хлебных единицах и граммах. Опасность с точки зрения расчёта дозы представляют именно продукты с низким гликемическим индексом, потому что ту дозу, которая была рассчитана только с учётом величины порции, нужно уменьшить."
#     },
#     {
#         "question": "Какие фрукты можно при диабете разных типов?",
#         "answer": "Фрукты отличаются друг от друга по гликемическому индексу (ГИ): высокий ГИ (60-70) имеют дыня, бананы, виноград, изюм; средний (47-59) – чернослив, черника, грейпфрут; низкий ГИ (34-46) у яблок, груш, апельсинов, персиков, слив, абрикосов, клубники. Некоторые из рекомендованных фруктов могут сильно различаться по составу в зависимости от сорта и условий произрастания. Поэтому стоит проверить после каждого приема пищи, не повлиял ли фрукт на повышение уровня сахара в крови. Для этого каждый человек, живущий с диабетом, должен вести дневник и записывать в него все продукты и блюда своего рациона. Диетические рекомендации не предусматривают запрет на употребление фруктов, даже если их гликемический индекс относительно высок. Для лиц с сахарным диабетом 1 типа нужно уметь пересчитывать углеводную нагрузку фруктов в хлебных единицах, чтобы компенсировать их прием с увеличением дозы инсулина. Людям с сахарным диабетом 2 типа следует избегать употребления большого количества (более 400 г в сутки) фруктов с высоким гликемическим индексом (бананы, дыня, очень спелые груши и сливы), а также засахаренных фруктов и цукатов, которые содержат очень много сахара и имеют высокую калорийность. Также не рекомендуется употреблять много джемов, варенья, подслащенных сиропов, консервированных фруктов в сладком маринаде, повидла, мармелада и фруктовых соков, особенно с добавленным сахаром."
#     },
#     {
#         "question": "Какие овощи разрешено есть при диабете?",
#         "answer": "Многие рекомендации по составлению рациона для людей с сахарным диабетом 1 и 2 типа советуют неограниченно увеличивать в диете долю овощей, таких как авокадо, брюссельская и цветная капуста, цуккини, брокколи, кабачки, лук, цикорий, зеленая фасоль, грибы, квашеная капуста, огурцы, оливки, сельдерей, баклажаны, зелень (шпинат, укроп, петрушка, кинза, зеленый лук), перец, редис. Готовить овощи лучше на пару, тушить, запекать в пергаменте или фольге, жарить на гриле без добавления масла. Лучше, если готовое блюдо будет слегка недоваренным, чем переваренным. Овощи al dente создают более долгое чувство насыщения, а углеводы из них всасываются медленнее. Люди с диабетом не могут позволить себе, чтобы в их овощном меню преобладали крахмалистые овощи. Следует ограничить: картофель, кукурузу, горох, вареную свеклу."
#     },
#     {
#         "question": "Для чего нужна система хлебных единиц?",
#         "answer": "За одну хлебную единицу принимают количество любого продукта, которое содержит от 10 до 12 граммов углеводов. Именно столько содержится в одном куске хлеба, поэтому и единицы называют хлебными (ХЕ). Узнать их содержание в том или ином продукте можно из специальных таблиц. Система хлебных единиц помогает определиться с дозой инсулина короткого действия, который вводят перед приемом пищи. Для этого нужно измерить уровень глюкозы и посчитать, сколько единиц содержит порция, которую планируется съесть. Согласно рекомендациям, в одной порции должно быть не более 8 ХЕ. На основании этих данных и рассчитывается необходимая доза инсулина."
#     },
#     {
#         "question": "Каким должно быть питание при сахарном диабете 1 типа?",
#         "answer": "При диабете 1 типа клетки поджелудочной железы не производят гормон инсулин, который обеспечивает проникновение глюкозы из кровяного русла в клетки. Основа лечения в этом случае — возмещение дефицита инсулина за счет введения его извне. При этом инсулин должен поступать в такой дозе, чтобы обеспечить транспорт всей поступающей с продуктами глюкозы из крови в клетки. Согласно современным представлениям, рацион правильного питания при диабете 1 типа соответствует полноценному, сбалансированному рациону по содержанию основных питательных веществ и калорийности. Подбирать только низкоуглеводные продукты при правильном подходе нет необходимости. Правила, которых необходимо придерживаться, при составлении меню: Белки и жиры людям, живущим с диабетом, можно потреблять без ограничений (при условии нормальной массы тела и с учетом калорийности). При избыточном весе рекомендуется ограничивать содержание жиров в рационе. Углеводы, содержащиеся в овощах, незначительно повышают уровень сахара в крови, поэтому большинство овощей можно есть практически без ограничений. Без подсчета уровня сахара можно есть зеленые листовые овощи, кабачки, перец, капусту, а также бобовые при условии потребления в умеренных количествах (около 200 г на прием пищи). Углеводы, которые содержатся в зерновых (хлеб), фруктах, некоторых овощах (картофель, кукуруза), молоке и молочных продуктах, а также в сахаре, нужно учитывать. Вести подсчет углеводов помогает система хлебных единиц."
#     },
#     {
#         "question": "Каким должно быть питание при сахарном диабете 2 типа?",
#         "answer": "Правильное, сбалансированное питание — неотъемлемая часть лечения диабета 2 типа. Ее калорийность рассчитывается исходя из массы тела: при нормальном весе количество калорий должно соответствовать затратам, при повышенном – быть ниже их (низкокалорийный рацион, гипокалорийная диета). Основные принципы питания при диабете 2 типа: Пища должна быть богата клетчаткой, которая тормозит усвоение сахара, препятствуя резкому повышению уровня глюкозы в крови. Этого достигают за счет высокого содержания в рационе овощей. В среднем уровень клетчатки в дневном меню должен составлять от 20 до 40 граммов. При приготовлении пищи лучше свести кулинарную обработку к минимуму. Важно помнить, что при измельчении, термической обработке содержащих углеводы продуктов глюкоза усваивается гораздо быстрее. Сахар и содержащие его продукты, в том числе чай, кофе с сахаром, должны быть максимально ограничены. Сахарозаменители можно есть в умеренных количествах, с учетом калорийности. Некалорийные сахарозаменители сахарин и аспартам можно потреблять по мере необходимости. Так называемые аналоги сахара ксилит, сорбит, фруктоза богаты калориями, поэтому их не рекомендуют при избыточном весе. Алкоголь вреден для здоровья, в том числе и при сахарном диабете. Он имеет высокую калорийность – 1 грамм чистого спирта содержит 7 ккал — и может способствовать повышению массы тела и ухудшению контроля над диабетом. Кроме того, при его потреблении увеличивается риск развития гипогликемии. Поэтому прием алкоголя нужно ограничить, а лучше – отказаться от него."
#     }
# ]
#     models = []
#     for item in data:
#         models.append(
#             FAQ(**item)
#         )
#     async with db.async_ses() as session:
#         session.add_all(models)
#         await session.commit()


if __name__ == '__main__':
    asyncio.run(main())
