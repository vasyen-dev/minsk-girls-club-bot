from database.models import Base
from database.requests import engine

print("🔄 Обновляем структуру базы данных...")
Base.metadata.create_all(engine)
print("✅ База данных обновлена!")