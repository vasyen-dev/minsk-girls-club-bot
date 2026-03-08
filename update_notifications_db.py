from database.models import Base, NotificationHistory
from database.requests import engine

print("🔄 Обновляем базу данных (добавляем таблицу notification_history)...")
Base.metadata.create_all(engine)
print("✅ Готово!")