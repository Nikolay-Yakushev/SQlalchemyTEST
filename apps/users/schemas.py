from typing import Optional, List
from pydantic import BaseModel, validator, EmailStr
from pydantic.json import UUID
from sqlalchemy import select, exists

from channels.schemas import ChannelOutput
from core.database import AsyncSessionLocal
from datetime import datetime

from models.models import User, Channel


class UserModel(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    hashed_password: Optional[str] = None
    is_active: Optional[bool] = True


class ChannelsInfo(BaseModel):
    id: UUID
    name: str
    date_joined: datetime


class UserOutputModel(UserModel):
    id: UUID
    email: str
    username: str
    is_active: bool
    date_created: Optional[datetime] = None
    channels: Optional[List[ChannelsInfo]]


class UserCreateModel(UserModel):
    email: EmailStr
    username: str
    hashed_password: str
    is_active: bool

    @validator("username")
    def check_username(cls, value):
        if not value.startswith("@"):
            raise ValueError("username should startswith @ sign")
        return value

    class Config:
        orm_mode = True


class AdditionalUserChecks:
    def __init__(self, session: AsyncSessionLocal):
        self.session = session

    async def validate_email_exists(self, user_sch: UserCreateModel):
        stm = select(exists(User).where(User.email == user_sch.email))
        res = await self.session.execute(stm)
        usr = res.scalars().all()
        if usr[0] is False:
            # user with such email does not exist
            return False
        return True

    async def validate_user_id(self, user_sch: UserCreateModel):
        stm = select(exists(User).where(User.id == user_sch.email))
        res = await self.session.execute(stm)
        usr = res.scalars().all()
        if usr[0] is False:
            # user with such email does not exist
            return False
        return True
