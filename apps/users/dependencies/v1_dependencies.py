from core.database import AsyncSessionLocal


class AsyncSessionManager:
    @classmethod
    async def get_session(cls):
        session = AsyncSessionLocal
        try:
            yield session
        finally:
            await session.close()
