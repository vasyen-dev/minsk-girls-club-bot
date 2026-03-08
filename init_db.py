from database.models import Base
from database.requests import engine, Session
from database.models import Interest
from database.promotion import init_promotion_packages
import asyncio

print("Создаем таблицы...")
Base.metadata.create_all(engine)

print("Добавляем интересы...")
interests_data = [
    {"name": "Йога", "category": "Красота и здоровье"},
    {"name": "Фитнес", "category": "Красота и здоровье"},
    {"name": "Макияж", "category": "Красота и здоровье"},
    {"name": "Маникюр", "category": "Красота и здоровье"},
    {"name": "SPA", "category": "Красота и здоровье"},
    {"name": "Мастер-классы", "category": "Творчество"},
    {"name": "Рисование", "category": "Творчество"},
    {"name": "Керамика", "category": "Творчество"},
    {"name": "Свечи", "category": "Творчество"},
    {"name": "Фотосессии", "category": "Творчество"},
    {"name": "Девичник", "category": "Общение"},
    {"name": "Бизнес-завтрак", "category": "Общение"},
    {"name": "Book club", "category": "Общение"},
    {"name": "Вайн-тайм", "category": "Общение"},
    {"name": "Психология", "category": "Общение"},
    {"name": "Танцы", "category": "Активности"},
    {"name": "Зумба", "category": "Активности"},
    {"name": "Прогулки", "category": "Активности"},
    {"name": "Кино", "category": "Развлечения"},
    {"name": "Настолки", "category": "Развлечения"},
    {"name": "Антикафе", "category": "Развлечения"},
    {"name": "Квизы", "category": "Развлечения"},
]

with Session() as session:
    if session.query(Interest).count() == 0:
        for item in interests_data:
            session.add(Interest(name=item["name"], category=item["category"]))
        session.commit()
        print("✅ Интересы добавлены!")
    else:
        print("ℹ️ Интересы уже есть")

asyncio.run(init_promotion_packages())
print("✅ База данных готова!")