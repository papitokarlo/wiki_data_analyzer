from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from wiki_generator.app.models import WikiData
from wiki_generator.config import settings



class SwitchDatabaseMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "https"):
            client = AsyncIOMotorClient(settings.MONGO_DB_URL)
            await init_beanie(
                database=client[str(settings.MONGO_DB_NAME)], document_models=[WikiData]
            )
        await self.app(scope, receive, send)