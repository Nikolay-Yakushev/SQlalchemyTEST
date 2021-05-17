from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from pydantic.json import UUID
from sqlalchemy import select, exists, and_

from core.database import AsyncSessionLocal
from models.models import Channel, Association


class ChannelBase(BaseModel):
    name: Optional[str] = None


class ChannelInput(ChannelBase):
    name: str


class ChannelOutput(ChannelBase):
    id: UUID
    name: str
    date_created: datetime


class AdditionalChannelChecks:
    def __init__(self, session: AsyncSessionLocal):
        self.session = session

    async def validate_group_exists(self, channel_id: UUID):
        stm = select(Channel).where(Channel.id == channel_id)
        res = await self.session.execute(stm)
        is_channel = res.scalars().all()
        if len(is_channel) == 0:
            # channel with such name does not exist
            return None, False
        return is_channel[0], True

    async def validate_user_in_group(self, channel_id: UUID, user_id: UUID):
        stm = select(exists(Association).where(and_(Association.channels_id == channel_id,
                                                    Association.users_id == user_id)))
        res = await self.session.execute(stm)
        is_joined = res.fetchone()
        if is_joined[0] is True:
            return True
        return False