import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class Button(SqlAlchemyBase):
    __tablename__ = 'buttons'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True,
                           autoincrement=True)
    text = sqlalchemy.Column(sqlalchemy.String)
    signs = sqlalchemy.Column(sqlalchemy.String)
    weight = sqlalchemy.Column(sqlalchemy.Integer)
    requirements = sqlalchemy.Column(sqlalchemy.String)
    actions = sqlalchemy.Column(sqlalchemy.String)
    ev1_id = sqlalchemy.Column(sqlalchemy.Integer,
                               sqlalchemy.ForeignKey("se_types.id"))
    ev1 = orm.relationship("SecondaryEventType", foreign_keys=[ev1_id])
    ev2_id = sqlalchemy.Column(sqlalchemy.Integer,
                               sqlalchemy.ForeignKey("se_types.id"))
    ev2 = orm.relationship("SecondaryEventType", foreign_keys=[ev2_id])
    ev3_id = sqlalchemy.Column(sqlalchemy.Integer,
                               sqlalchemy.ForeignKey("se_types.id"))
    ev3 = orm.relationship("SecondaryEventType", foreign_keys=[ev3_id])