import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class SecondaryEventType(SqlAlchemyBase):
    __tablename__ = 'se_types'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    type = sqlalchemy.Column(sqlalchemy.String)
    requirements = sqlalchemy.Column(sqlalchemy.String)
    weight = sqlalchemy.Column(sqlalchemy.Integer)
    b1_id = sqlalchemy.Column(sqlalchemy.Integer,
                              sqlalchemy.ForeignKey("buttons.id"))
    b1 = orm.relationship('Button', foreign_keys=[b1_id])
    b2_id = sqlalchemy.Column(sqlalchemy.Integer,
                              sqlalchemy.ForeignKey("buttons.id"))
    b2 = orm.relationship('Button', foreign_keys=[b2_id])
    tags = sqlalchemy.Column(sqlalchemy.String)