import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class NormalEventText(SqlAlchemyBase):
    __tablename__ = 'ne_texts'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    type_id = sqlalchemy.Column(sqlalchemy.Integer,
                             sqlalchemy.ForeignKey('ne_types.id'))
    type = orm.relationship("NormalEventType", foreign_keys=[type_id])
    text = sqlalchemy.Column(sqlalchemy.String)
    tags = sqlalchemy.Column(sqlalchemy.String)