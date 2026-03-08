import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from handlers import registration, profile, create_event, moderation, events, my_plans, friends, chat, admin_stats, notifications
from scheduler import on_startup
from config import BOT_TOKEN, ADMIN_IDS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Подключаем все роутеры
dp.include_router(registration.router)
dp.include_router(profile.router)
dp.include_router(create_event.router)
dp.include_router(moderation.router)
dp.include_router(events.router)
dp.include_router(my_plans.router)
dp.include_router(friends.router)
dp.include_router(chat.router)
dp.include_router(admin_stats.router)

async def main():
    # Запускаем планировщик
    await on_startup()
    
    # Запускаем систему уведомлений
    from handlers.notifications import on_startup_notifications
    await on_startup_notifications(bot)
    
    logger.info("🚀 Бот SVOI Minsk Girls запущен!")
    print(f"🔍 Администраторы: {ADMIN_IDS}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())