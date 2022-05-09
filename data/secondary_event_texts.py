import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class SecondaryEventText(SqlAlchemyBase):
    __tablename__ = 'se_texts'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    type_id = sqlalchemy.Column(sqlalchemy.Integer,
                             sqlalchemy.ForeignKey('se_types.id'))
    type = orm.relationship("SecondaryEventType", foreign_keys=[type_id])
    text = sqlalchemy.Column(sqlalchemy.String)