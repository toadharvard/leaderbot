from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.orm import scoped_session
from sqlalchemy import create_engine


class ORMModel(DeclarativeBase):
    __abstract__ = True


engine = create_engine("sqlite:///memory.db", echo=True)
db = scoped_session(sessionmaker(bind=engine))()


def init_db():
    ORMModel.metadata.create_all(bind=engine)
