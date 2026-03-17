import threading
from flask import Flask
import os
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from handlers import registration, profile, create_event, moderation, events, my_plans, friends, chat, admin_stats, notifications
from scheduler import on_startup
from config import BOT_TOKEN, ADMIN_IDS

# ---------- HEALTH CHECK SERVER (для Render) ----------
health_app = Flask(__name__)

@health_app.route('/health')
def health():
    return "OK", 200

@health_app.route('/')
def home():
    return "Minsk Girls Club Bot is running!", 200

def run_health_server():
    port = int(os.environ.get('PORT', 10000))
    health_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# Запускаем health-сервер в фоновом потоке
threading.Thread(target=run_health_server, daemon=True).start()
print(f"✅ Health check server started on port {os.environ.get('PORT', 10000)}")

# ---------- ОСНОВНОЙ БОТ ----------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Проверка токена
if not BOT_TOKEN:
    raise ValueError("Нет токена! Создай файл .env и добавь BOT_TOKEN=...")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Подключаем все роутеры
print("🔹 Подключение роутеров...")
dp.include_router(registration.router)
dp.include_router(profile.router)
dp.include_router(create_event.router)
dp.include_router(moderation.router)  # ← ВАЖНО: роутер модерации подключен!
dp.include_router(events.router)
dp.include_router(my_plans.router)
dp.include_router(friends.router)
dp.include_router(chat.router)
dp.include_router(admin_stats.router)
print("✅ Все роутеры подключены")

async def main():
    # Запускаем планировщик
    await on_startup()
    
    # Запускаем систему уведомлений
    from handlers.notifications import on_startup_notifications
    await on_startup_notifications(bot)
    
    logger.info("🚀 Бот Minsk Girls Club запущен!")
    print(f"🔍 Администраторы: {ADMIN_IDS}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())