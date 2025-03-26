import sys
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from config import settings
from routers import base

ADMIN_ID = settings.ADMIN_ID 
API_TOKEN = settings.API_TOKEN

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

dp.include_routers(
    base.router
)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(asctime)s %(levelname)s %(message)s")
    logger = logging.getLogger(__name__)
    asyncio.run(main())
