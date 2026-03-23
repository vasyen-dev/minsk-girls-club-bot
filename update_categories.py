from database.requests import Session
from database.models import Interest

# 6 категорий для мероприятий
CATEGORIES = [
    {"name": "🎨 Творчество", "category": "Мероприятия"},
    {"name": "💬 Общение", "category": "Мероприятия"},
    {"name": "🏃‍♀️ Активности", "category": "Мероприятия"},
    {"name": "🎬 Развлечения", "category": "Мероприятия"},
    {"name": "💄 Красота и здоровье", "category": "Мероприятия"},
    {"name": "📚 Образование и развитие", "category": "Мероприятия"},
]

print("🔄 Обновляем таблицу интересов...")
print("=" * 40)

with Session() as session:
    # Удаляем все старые интересы
    old_count = session.query(Interest).count()
    session.query(Interest).delete()
    print(f"🗑️ Удалено старых интересов: {old_count}")
    
    # Добавляем 6 новых категорий
    for cat in CATEGORIES:
        interest = Interest(name=cat["name"], category=cat["category"])
        session.add(interest)
    
    session.commit()
    print(f"✅ Добавлено новых категорий: {len(CATEGORIES)}")
    
    # Проверяем
    new_interests = session.query(Interest).all()
    print("\n📋 Текущий список:")
    for i in new_interests:
        print(f"   • {i.name}")

print("=" * 40)
print("✅ Готово!")