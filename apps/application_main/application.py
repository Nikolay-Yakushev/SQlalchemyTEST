from fastapi import FastAPI
import uvicorn
from starlette.middleware.cors import CORSMiddleware
from channels.views import v2_route
from users.views import v1_route


def _get_app():
    _app = FastAPI()
    _app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    _app.include_router(v1_route)
    _app.include_router(v2_route)
    # @app1.middleware('http')
    # async def get_session_middleware(request: Request, call_next):
    #     async with AsyncSessionLocal as session:
    #         request.state.db_session = session
    #         return await call_next(request)
    #
    # _app.mount("/users", app1, "/app1")
    return _app


if __name__ == "__main__":
    from dotenv import load_dotenv, find_dotenv

    load_dotenv(find_dotenv(filename="my_dotenv.env.dev"))
    uvicorn.run(app=_get_app())
