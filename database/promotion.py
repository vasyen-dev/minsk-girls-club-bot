from sqlalchemy import select, and_, desc
from datetime import datetime, timedelta
from .models import PromotionPackage, PromotedEvent, Event
from .requests import Session

async def init_promotion_packages():
    """Создать начальные пакеты продвижения"""
    packages = [
        {
            "name": "🌱 Лайт",
            "description": "Поднять мероприятие в топ на 24 часа",
            "price": 500,
            "duration_hours": 24,
            "priority_level": 1
        },
        {
            "name": "🔥 VIP",
            "description": "VIP-статус на 3 дня + закреп в топе",
            "price": 1500,
            "duration_hours": 72,
            "priority_level": 2
        },
        {
            "name": "👑 Премиум",
            "description": "Неделя в топе + отдельный VIP-раздел",
            "price": 3000,
            "duration_hours": 168,
            "priority_level": 3
        }
    ]
    
    with Session() as session:
        if session.query(PromotionPackage).count() == 0:
            for p in packages:
                package = PromotionPackage(
                    name=p["name"],
                    description=p["description"],
                    price=p["price"],
                    duration_hours=p["duration_hours"],
                    priority_level=p["priority_level"]
                )
                session.add(package)
            session.commit()
            print("✅ Пакеты продвижения добавлены!")
        else:
            print("ℹ️ Пакеты уже существуют")

async def get_all_packages():
    """Получить все активные пакеты"""
    with Session() as session:
        return session.execute(
            select(PromotionPackage).where(PromotionPackage.is_active == True)
        ).scalars().all()

async def get_package(package_id):
    """Получить пакет по ID"""
    with Session() as session:
        return session.get(PromotionPackage, package_id)

async def promote_event(event_id, package_id, payment_id=None):
    """Активировать продвижение"""
    with Session() as session:
        package = session.get(PromotionPackage, package_id)
        event = session.get(Event, event_id)
        
        if not package or not event:
            return None
        
        expires_at = datetime.now() + timedelta(hours=package.duration_hours)
        
        promoted = PromotedEvent(
            event_id=event_id,
            package_id=package_id,
            expires_at=expires_at,
            payment_status='paid' if payment_id else 'pending',
            payment_id=payment_id
        )
        
        event.priority = package.priority_level
        
        session.add(promoted)
        session.commit()
        return promoted