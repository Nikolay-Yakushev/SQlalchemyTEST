import uuid
import sqlalchemy
from sqlalchemy import func, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, class_mapper, ColumnProperty, relationship


class BaseMixin(object):
    def as_dict(self):
        result = {}
        for prop in class_mapper(self.__class__).iterate_properties:
            if isinstance(prop, ColumnProperty):
                result[prop.key] = getattr(self, prop.key)
        return result


Base = declarative_base()

association_table = sqlalchemy.Table(
    "association",
    Base.metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column(
        "users_id", UUID(as_uuid=True), sqlalchemy.ForeignKey("users.id")
    ),
    sqlalchemy.Column(
        "channels_id", UUID(as_uuid=True), sqlalchemy.ForeignKey("channels.id")
    ),
    sqlalchemy.Column(
        "date_joined", sqlalchemy.DateTime, default=func.now(), nullable=False
    ),
)

user_table = sqlalchemy.Table(
    "users",
    Base.metadata,
    sqlalchemy.Column(
        "id",
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    ),
    sqlalchemy.Column("email", sqlalchemy.String(40), unique=True, index=True),
    sqlalchemy.Column("username", sqlalchemy.String(100)),
    sqlalchemy.Column("hashed_password", sqlalchemy.String()),
    sqlalchemy.Column(
        "is_active",
        sqlalchemy.Boolean(),
        server_default=sqlalchemy.sql.expression.true(),
        nullable=False,
    ),
    sqlalchemy.Column(
        "date_created", sqlalchemy.DateTime(), default=func.now(), nullable=False
    ),
)

channel_table = sqlalchemy.Table(
    "channels",
    Base.metadata,
    sqlalchemy.Column(
        "id",
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    ),
    sqlalchemy.Column("name", sqlalchemy.String(40), unique=True),
    sqlalchemy.Column(
        "date_created", sqlalchemy.DateTime(), default=func.now(), nullable=False
    ),
)


class Association(Base):
    __table__ = association_table
    __tablename__ = "association"
    __table_args__ = (PrimaryKeyConstraint("users_id", "channels_id"),)
    user_assoc = relationship("User", back_populates="channels")
    channels_assoc = relationship("Channel", back_populates="users")
    __mapper_args__ = {"eager_defaults": True}


class User(BaseMixin, Base):
    __table__ = user_table
    __tablename__ = "users"
    channels = relationship("Association", back_populates="user_assoc")
    __mapper_args__ = {"eager_defaults": True}


class Channel(BaseMixin, Base):
    __table__ = channel_table
    __tablename__ = "channels"
    users = relationship("Association", back_populates="channels_assoc")
    __mapper_args__ = {"eager_defaults": True}
