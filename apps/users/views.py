from typing import List, Callable
from uuid import UUID

import sqlalchemy.orm
from fastapi import HTTPException, APIRouter
from fastapi.routing import APIRoute
from sqlalchemy import insert, delete, update
from sqlalchemy.orm import selectinload
from starlette.requests import Request
from sqlalchemy.future import select
from starlette.responses import Response
from channels.schemas import AdditionalChannelChecks
from core.database import AsyncSessionLocal
from models.models import User, Association, Channel

from .schemas import UserCreateModel, UserOutputModel, UserModel, AdditionalUserChecks
from pydantic import parse_obj_as

class DatabaseRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            async with AsyncSessionLocal as session:
                request.state.db_session = session
            response: Response = await original_route_handler(request)
            return response

        return custom_route_handler


v1_route = APIRouter(route_class=DatabaseRoute, prefix="/users")


def get_user_channels(session, user_model):
    channels_info_grouped = []
    for assoc_model in user_model.channels:
        channels_info = {
            "id": assoc_model.channels_assoc.id,
            "name": assoc_model.channels_assoc.name,
            "date_joined": assoc_model.date_joined,
        }
        channels_info_grouped.append(channels_info)

    return channels_info_grouped


@v1_route.get("/all")
async def get_all_users(request: Request):
    db_session = request.state.db_session
    stmt = select(User).options(selectinload(User.channels))
    query = await db_session.execute(stmt)
    users = query.scalars().all()
    list_users: List[dict] = []
    for user_model in users:
        if len(user_model.channels) != 0:
            channels_inf = await db_session.run_sync(get_user_channels, user_model)
        else:
            channels_inf = []
        dict_model = user_model.as_dict()
        dict_model.update({"channels": channels_inf})
        list_users.append(dict_model)
    parsed_list = parse_obj_as(List[UserOutputModel], list_users)
    return {"users": parsed_list}


@v1_route.get(
    "/{user_id}",
    response_model=UserOutputModel,
    response_model_exclude={"hashed_password"},
)
async def get_detail_user(user_id: str, request: Request):
    db_session = request.state.db_session
    stm = select(User).where(User.id == UUID(user_id))
    obj = await db_session.execute(stm)
    user_row = obj.fetchone()
    if not user_row:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} not found")
    user_form_row = user_row[0]
    user = user_form_row
    return UserOutputModel(**user.as_dict())


@v1_route.delete(
    "/{user_id}",
    response_model=UserOutputModel,
    response_model_exclude={"hashed_password"},
    status_code=200,
)
async def delete_user(user_id: str, request: Request):
    db_session = request.state.db_session
    async with db_session.begin():
        stm = delete(User).where(User.id == UUID(user_id)).returning(User)
        obj = await db_session.execute(stm)
        user_row = obj.fetchone()
    if not user_row:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} not found")
    user_from_row = User(**dict(user_row))
    await db_session.flush()
    user_deleted = user_from_row

    return UserOutputModel(**user_deleted.as_dict())


@v1_route.put("/{user_id}", response_model=UserOutputModel, status_code=200)
async def update_user(request: Request, user_id: str, user: UserModel):
    db_session = request.state.db_session
    async with db_session.begin():
        stm = (
            update(User)
                .where(User.id == UUID(user_id))
                .values(**user.dict())
                .returning(User)
        )

        obj = await db_session.execute(stm)
        await db_session.flush()
        user = obj.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} not found")
    return UserOutputModel(**dict(user))


@v1_route.post("/", response_model=UserOutputModel, status_code=201)
async def add_new_user(request: Request, user: UserCreateModel):
    db_session = request.state.db_session
    #validation = AdditionalUserChecks(db_session)
    #
    # async with db_session.begin():
    #     is_email = await validation.validate_email_exists(user)
    # if is_email:
    #     raise HTTPException(
    #         status_code=400, detail=f"Email {user.email} already exists"
    #     )
    async with db_session.begin():
        #stm = insert(User).values(**user.dict()).returning(User)
        new_user=User(**user.dict())
        db_session.add(new_user)
        try:
            result = await db_session.flush()
        except Exception as e:
            await db_session.rollback()
            await db_session.close()
            raise HTTPException(status_code=500, detail=f"Email {user.email} already exists")
    usr = User(**dict(new_user))
    return UserOutputModel(**usr.as_dict())


def create_rel(session, channel: Channel, user_id: str):
    stmt = insert(Association).values(users_id=user_id, channels_id=channel.id)
    session.execute(stmt)


def run_greenlet_sync(session, stmt):
    session.execute(stmt)


@v1_route.put("/add_to_group/{user_id}", status_code=200)
async def update_user(request: Request, user_id: UUID, channel_id):
    db_session = request.state.db_session
    validation = AdditionalChannelChecks(db_session)
    #async with db_session.begin():
        #channel, exists = await validation.validate_group_exists(channel_id)
        #is_user_in_group = await validation.validate_user_in_group(channel_id, user_id)
    # if exists is False:
    #     raise HTTPException(
    #         status_code=404, detail=f"Channel {channel_id} does not exist"
    #     )
    # if is_user_in_group:
    #     raise HTTPException(
    #         status_code=404, detail=f"User {user_id} is already in group with id {channel_id}"
    #     )

    async with db_session as session:
        async with db_session.begin():
            # todo как insert в AssosiationTable не вызывая при этом greenlet и run_sync
            stmt_ins = insert(Association).values(users_id=user_id, channels_id=channel_id)
            #await session.run_sync(create_rel, channel, user_id)
            await session.run_sync(run_greenlet_sync,
                                   stmt=stmt_ins)
            result = await db_session.flush()
    return {"ok": True}
