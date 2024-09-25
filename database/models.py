
from sqlalchemy import String, Integer, DateTime, Boolean, BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from werkzeug.security import check_password_hash, generate_password_hash


class Base(DeclarativeBase):
    pass


class UserAuth(Base):
    __tablename__ = "user_auth"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password: Mapped[str] = mapped_column(String, name='password')
    is_admin: Mapped[bool] = mapped_column(Boolean, default=True)

    def set_password(self, password: str):
        self.password = generate_password_hash(password)
    #
    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password, password)

    # @classmethod
    def hash_password(cls, password: str):
        return generate_password_hash(password)


class FAQ(Base):
    __tablename__ = 'faq'

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(Integer, nullable=True)
    # images_list: Mapped[JSONB] = mapped_column(JSONB, nullable=True)
    question: Mapped[str] = mapped_column(String, nullable=True)
    answer: Mapped[str] = mapped_column(String, nullable=True)

    def get_data(self):
        return {
            'question': self.question,
            'answer': self.answer,
        }


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)

    tg_id: Mapped[str] = mapped_column(String(255), unique=True)
    username: Mapped[str] = mapped_column(String(255), unique=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    deleted: Mapped[bool] = mapped_column(default=False)
    timezone: Mapped[int] = mapped_column(nullable=True)


class FoodDiary(Base):
    __tablename__ = 'foods_diarys'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    dish_name: Mapped[str] = mapped_column(String, nullable=True)
    calories: Mapped[str] = mapped_column(String, nullable=True)
    proteins: Mapped[str] = mapped_column(String, nullable=True)
    proteins_percent: Mapped[str] = mapped_column(String, nullable=True)
    fats: Mapped[str] = mapped_column(String, nullable=True)
    fats_percent: Mapped[str] = mapped_column(String, nullable=True)
    carbohydrates: Mapped[str] = mapped_column(String, nullable=True)
    carbohydrates_percent: Mapped[str] = mapped_column(String, nullable=True)
    bread_units: Mapped[str] = mapped_column(String, nullable=True)
    total_weight: Mapped[str] = mapped_column(String, nullable=True)
    glycemic_index: Mapped[str] = mapped_column(String, nullable=True)
    protein_bje: Mapped[str] = mapped_column(String, nullable=True)
    fats_bje: Mapped[str] = mapped_column(String, nullable=True)
    calories_bje: Mapped[str] = mapped_column(String, nullable=True)
    bje_units: Mapped[str] = mapped_column(String, nullable=True)
    send_notif: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime)
    updated_at: Mapped[DateTime] = mapped_column(DateTime)

    def __str__(self):
        proteins_percent = f'({self.proteins_percent}%)' if self.proteins_percent else ''
        fats_percent = f'({self.fats_percent}%)' if self.fats_percent else ''
        carbohydrates_percent = f'({self.carbohydrates_percent}%)' if self.carbohydrates_percent else ''
        return (
            f'{self.created_at.strftime("%H:%M") if self.created_at else ""}\n'
            f'{self.dish_name} ({self.total_weight} г.)\n'
            f'Калории: {self.calories} ккал\n'
            f'Белки: {self.proteins} г. {proteins_percent}\n'
            f'Жиры: {self.fats} г. {fats_percent}\n'
            f'Углеводы: {self.carbohydrates} г. {carbohydrates_percent} ({self.bread_units} ХЕ)\n'
            f'Гликемический индекс: {self.glycemic_index}\n'
            f'БЖЕ: {self.protein_bje}\n'
            f'    Протеин: {self.protein_bje} г.\n'
            f'    Жиры: {self.fats_bje} г.\n'
            # f'    Калории: {self.calories_bje}ккал\n'
        )

    def get_data(self):
        return {
            'dish_name': self.dish_name,
            'calories': self.calories,
            'proteins': self.proteins,
            'fats': self.fats,
            'fats_percent': self.fats_percent,
            'carbohydrates': self.carbohydrates,
            'carbohydrates_percent': self.carbohydrates_percent,
            'bread_units': self.bread_units,
            'total_weight': self.total_weight,
            'glycemic_index': self.glycemic_index,
            'protein_bje': self.protein_bje,
            'fats_bje': self.fats_bje,
            'calories_bje': self.calories_bje,
            'bje_units': self.bje_units,
            'updated_at': str(self.updated_at),
            'updated_at_without_time': str(self.updated_at.strftime('%d-%m-%Y'))
        }
