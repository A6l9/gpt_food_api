
from sqlalchemy import String, Integer, DateTime, Boolean, Interval
from sqlalchemy.dialects.postgresql import JSONB
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

