import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec

ORMBase = dec.declarative_base()

__factory = None
global_session = None


def create_session():
    global __factory
    return __factory()


def global_init(db_file):
    global __factory, global_session

    if __factory:
        return

    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
    print(f'Подключение к базе данных..')

    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    from . import models

    ORMBase.metadata.create_all(engine)
    global_session = create_session()
