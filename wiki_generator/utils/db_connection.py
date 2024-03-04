from motor.motor_asyncio import AsyncIOMotorClient

from wiki_generator.config import settings


client = AsyncIOMotorClient(settings.MONGO_DB_URL)
db = client.get_database(settings.MONGO_DB_NAME)
