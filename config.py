import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Список админов (ID через запятую)
admin_ids_str = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]
CLUB_CHAT_LINK = os.getenv("CLUB_CHAT_LINK", "")

# Проверка, что токен загружен
if not BOT_TOKEN:
    raise ValueError("Нет токена! Создай файл .env и добавь BOT_TOKEN=...")

# ОТЛАДКА: выводим информацию при запуске
print("🔍 ЗАГРУЗКА КОНФИГУРАЦИИ:")
print(f"🔍 ADMIN_IDS_STR = '{admin_ids_str}'")
print(f"🔍 ADMIN_IDS = {ADMIN_IDS}")
print(f"🔍 BOT_TOKEN = {BOT_TOKEN[:10]}...")