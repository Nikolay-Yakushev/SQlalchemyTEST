from typing import Callable, List

from fastapi import APIRouter
from fastapi.routing import APIRoute
from pydantic import parse_obj_as
from sqlalchemy import select, insert
from starlette.requests import Request
from starlette.responses import Response

from channels.schemas import ChannelOutput, ChannelInput
from core.database import AsyncSessionLocal
from models.models import Channel, Association


class DatabaseRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            async with AsyncSessionLocal as session:
                request.state.db_session = session
            response: Response = await original_route_handler(request)
            return response

        return custom_route_handler


v2_route = APIRouter(route_class=DatabaseRoute, prefix="/channels")


@v2_route.get("/all")
async def get_all_channels(request: Request):
    db_session = request.state.db_session
    stm = select(Channel)
    query = await db_session.execute(stm)
    channels = query.scalars().all()
    list_channels: List[dict] = []
    for channel_model in channels:
        list_channels.append(channel_model.as_dict())
    parsed_list = parse_obj_as(List[ChannelOutput], list_channels)
    return {"channels": parsed_list}


@v2_route.post("/add", response_model=ChannelOutput, status_code=201)
async def add_new_channel(request: Request, channel: ChannelInput):
    db_session = request.state.db_session
    async with db_session.begin():
        stm = insert(Channel).values(**channel.dict()).returning(Channel)
        obj = await db_session.execute(stm)
        await db_session.flush()
        new_channel = obj.fetchone()
    return ChannelOutput(**dict(new_channel))
