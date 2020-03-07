from sqlalchemy import Column, Integer, String
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from .db_session import ORMBase


class User(ORMBase, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer,
                primary_key=True,
                autoincrement=True)
    name = Column(String,
                  nullable=False)
    email = Column(String,
                   nullable=False,
                   unique=True)
    hashed_password = Column(String,
                             nullable=False)

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)