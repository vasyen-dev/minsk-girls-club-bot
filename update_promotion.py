from database.models import Base
from database.requests import engine
from database.promotion import init_promotion_packages
import asyncio

print("Обновляем структуру БД...")
Base.metadata.create_all(engine)

asyncio.run(init_promotion_packages())
print("✅ База данных обновлена!")