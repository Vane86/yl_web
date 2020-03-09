from sqlalchemy import orm, Column, Integer, String, DateTime, ForeignKey, Table
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import datetime

from .db_session import ORMBase


group2user = Table('group2user', ORMBase.metadata,
                   Column('group_id', Integer, ForeignKey('groups.id')),
                   Column('user_id', Integer, ForeignKey('users.id')))


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

    groups = orm.relation('Group', secondary='group2user', back_populates='users')

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)


class Group(ORMBase):
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    max_members = Column(Integer, nullable=False)
    admin_id = Column(Integer, ForeignKey('users.id'))

    admin = orm.relation('User')
    users = orm.relation('User', secondary='group2user', back_populates='groups')
    # tasks - list of Task instances

    def __init__(self, name, max_members, admin_id):
        self.name = name
        self.max_members = max_members
        self.admin_id = admin_id


class Task(ORMBase):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'))
    performer_id = Column(Integer, ForeignKey('users.id'))
    group_id = Column(Integer, ForeignKey('groups.id'))
    priority = Column(Integer, nullable=False)  # 0 - high, 1 - medium, 2 - low
    description = Column(String, nullable=False)
    status = Column(Integer, nullable=True, default=0)  # 0 - open, 1 - closed
    creation_time = Column(DateTime, nullable=False, default=datetime.datetime.now)

    author = orm.relation('User', foreign_keys=[author_id])
    performer = orm.relation('User', foreign_keys=[performer_id])
    group = orm.relation('Group', backref='tasks')

    def __init__(self, name, author_id, performer_id, group_id, priority, description):
        self.name = name
        self.author_id = author_id
        self.performer_id = performer_id
        self.group_id = group_id
        self.priority = priority
        self.description = description
