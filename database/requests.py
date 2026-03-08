from sqlalchemy import create_engine, select, update, delete, and_, desc
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from .models import Base, User, Interest, Event, EventParticipant, ModerationQueue, PromotionPackage, PromotedEvent, Friend

# Создаем подключение к БД
engine = create_engine('sqlite:///svoi_minsk_girls.db', echo=True)
Session = sessionmaker(bind=engine)

# Создаем таблицы (если их нет)
Base.metadata.create_all(engine)

# ----- ПОЛЬЗОВАТЕЛИ -----

async def add_user(user_id, username, name, age, district, bio=None, photo_file_id=None, instagram=None):
    """Добавить нового пользователя"""
    print(f"🔍 ДОБАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯ: {user_id}")
    with Session() as session:
        user = User(
            user_id=user_id,
            username=username,
            name=name,
            age=age,
            district=district,
            bio=bio,
            photo_file_id=photo_file_id,
            instagram=instagram
        )
        session.add(user)
        session.commit()
        print(f"✅ Пользователь {user_id} добавлен")
        return user

async def get_user(user_id):
    """Получить пользователя по ID"""
    with Session() as session:
        return session.get(User, user_id)

async def user_exists(user_id):
    """Проверить, есть ли пользователь"""
    with Session() as session:
        return session.get(User, user_id) is not None

async def update_user(user_id, **kwargs):
    """Обновить данные пользователя"""
    print(f"🔍 ОБНОВЛЕНИЕ ПОЛЬЗОВАТЕЛЯ: {user_id}, данные: {kwargs}")
    with Session() as session:
        user = session.get(User, user_id)
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        session.commit()
        print(f"✅ Пользователь {user_id} обновлен")

async def delete_user(user_id: int):
    """Полное удаление пользователя"""
    print(f"🔍 УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЯ: {user_id}")
    with Session() as session:
        user = session.get(User, user_id)
        if user:
            session.delete(user)
            session.commit()
            print(f"✅ Пользователь {user_id} удален")
            return True
        print(f"❌ Пользователь {user_id} не найден")
        return False

# ----- ИНТЕРЕСЫ -----

async def get_all_interests():
    """Получить все интересы"""
    with Session() as session:
        return session.execute(select(Interest)).scalars().all()

async def add_user_interests(user_id, interest_ids):
    """Добавить интересы пользователю"""
    print(f"🔍 ДОБАВЛЕНИЕ ИНТЕРЕСОВ пользователю {user_id}: {interest_ids}")
    with Session() as session:
        user = session.get(User, user_id)
        interests = session.execute(
            select(Interest).where(Interest.id.in_(interest_ids))
        ).scalars().all()
        user.interests = interests
        session.commit()
        print(f"✅ Интересы пользователя {user_id} обновлены")

async def get_user_interests(user_id):
    """Получить интересы пользователя"""
    with Session() as session:
        user = session.get(User, user_id)
        if not user:
            return []
        interests = list(user.interests)
        return interests

async def get_category_name(category_id):
    """Получить название категории по ID"""
    if not category_id:
        return "Не указана"
    with Session() as session:
        category = session.get(Interest, category_id)
        return category.name if category else "Не указана"

# ----- СОБЫТИЯ -----

async def add_event(creator_id, title, description, category, photo_file_id, 
                    address, latitude, longitude, district, event_date, price, 
                    max_participants, chat_link=None, chat_id=None):
    """Добавить новое мероприятие"""
    print(f"🔍 ДОБАВЛЕНИЕ МЕРОПРИЯТИЯ: {title}")
    with Session() as session:
        # Находим ID категории (интереса) по названию
        category_obj = session.execute(
            select(Interest).where(Interest.name == category)
        ).scalar_one_or_none()
        
        if not category_obj:
            # Если категория не найдена, создаем новую
            print(f"🔍 Категория {category} не найдена, создаем новую")
            category_obj = Interest(name=category, category=category)
            session.add(category_obj)
            session.flush()
        
        event = Event(
            creator_id=creator_id,
            title=title,
            description=description,
            category_id=category_obj.id,
            photo_file_id=photo_file_id,
            address=address,
            latitude=latitude,
            longitude=longitude,
            district=district,
            event_date=event_date,
            price=price,
            max_participants=max_participants,
            current_participants=0,
            status='pending',
            priority=0,
            chat_link=chat_link,
            chat_id=chat_id
        )
        session.add(event)
        session.commit()
        print(f"✅ Мероприятие сохранено с ID: {event.event_id}")
        return event.event_id

async def check_expired_events():
    """Проверить прошедшие мероприятия"""
    with Session() as session:
        now = datetime.now()
        expired = session.execute(
            select(Event).where(
                and_(
                    Event.event_date < now,
                    Event.status.in_(['approved', 'pending'])
                )
            )
        ).scalars().all()
        
        count = 0
        for event in expired:
            event.status = 'completed'
            count += 1
        
        if count > 0:
            session.commit()
        return count

async def get_active_events(category=None, district=None, limit=20):
    """Получить активные мероприятия (одобренные и будущие)"""
    print(f"🔍 get_active_events: category={category}, district={district}, limit={limit}")
    with Session() as session:
        now = datetime.now()
        
        # Базовый запрос: только одобренные и будущие
        query = select(Event).where(
            and_(
                Event.status == 'approved',
                Event.event_date > now
            )
        )
        
        # Добавляем фильтры, если они указаны
        if category:
            query = query.where(Event.category_id == category)
        if district and district != "Весь Минск":
            query = query.where(Event.district == district)
        
        # Сортируем: сначала VIP, потом по дате
        query = query.order_by(desc(Event.priority), Event.event_date)
        query = query.limit(limit)
        
        events = session.execute(query).scalars().all()
        print(f"🔍 Найдено мероприятий: {len(events)}")
        return events

async def get_event(event_id):
    """Получить мероприятие по ID"""
    print(f"🔍 ВЫЗОВ get_event для ID {event_id}")
    with Session() as session:
        event = session.get(Event, event_id)
        return event

# ----- УЧАСТНИКИ -----

async def add_participant(event_id, user_id):
    """Записать пользователя на мероприятие"""
    print(f"🔍 ЗАПИСЬ на мероприятие {event_id} пользователя {user_id}")
    with Session() as session:
        # Проверяем, не записан ли уже
        existing = session.execute(
            select(EventParticipant).where(
                and_(
                    EventParticipant.event_id == event_id,
                    EventParticipant.user_id == user_id
                )
            )
        ).first()
        
        if existing:
            print(f"❌ Пользователь {user_id} уже записан")
            return False
        
        participant = EventParticipant(
            event_id=event_id,
            user_id=user_id
        )
        session.add(participant)
        
        # Увеличиваем счетчик участников
        event = session.get(Event, event_id)
        if event:
            event.current_participants += 1
        
        session.commit()
        print(f"✅ Пользователь {user_id} записан на мероприятие {event_id}")
        return True

async def remove_participant(event_id, user_id):
    """Отменить запись пользователя"""
    print(f"🔍 ОТМЕНА записи на мероприятие {event_id} пользователя {user_id}")
    with Session() as session:
        participant = session.execute(
            select(EventParticipant).where(
                and_(
                    EventParticipant.event_id == event_id,
                    EventParticipant.user_id == user_id
                )
            )
        ).scalar_one_or_none()
        
        if not participant:
            print(f"❌ Запись не найдена")
            return False
        
        session.delete(participant)
        
        # Уменьшаем счетчик участников
        event = session.get(Event, event_id)
        if event and event.current_participants > 0:
            event.current_participants -= 1
        
        session.commit()
        print(f"✅ Запись отменена")
        return True

async def get_event_participants(event_id):
    """Получить список участников мероприятия"""
    print(f"🔍 ПОЛУЧЕНИЕ УЧАСТНИКОВ для мероприятия {event_id}")
    with Session() as session:
        participants = session.execute(
            select(EventParticipant).where(EventParticipant.event_id == event_id)
        ).scalars().all()
        return participants

async def get_user_events(user_id):
    """Получить мероприятия, на которые записан пользователь"""
    print(f"🔍 ПОЛУЧЕНИЕ ЗАПИСЕЙ пользователя {user_id}")
    with Session() as session:
        events = session.execute(
            select(Event).join(EventParticipant).where(
                EventParticipant.user_id == user_id
            ).order_by(Event.event_date)
        ).scalars().all()
        return events

async def get_user_created_events(user_id):
    """Получить мероприятия, созданные пользователем"""
    print(f"🔍 ПОЛУЧЕНИЕ СОЗДАННЫХ мероприятий пользователя {user_id}")
    with Session() as session:
        events = session.execute(
            select(Event).where(Event.creator_id == user_id)
            .order_by(Event.event_date)
        ).scalars().all()
        return events

# ----- МОДЕРАЦИЯ -----

async def get_pending_events():
    """Получить все мероприятия на модерации"""
    print("🔍 ВЫЗОВ get_pending_events")
    with Session() as session:
        events = session.execute(
            select(Event).where(Event.status == 'pending')
        ).scalars().all()
        print(f"🔍 Найдено мероприятий на модерации: {len(events)}")
        return events

async def approve_event(event_id):
    """Опубликовать мероприятие"""
    print(f"🔍 ВЫЗОВ approve_event для ID {event_id}")
    with Session() as session:
        event = session.get(Event, event_id)
        if event:
            event.status = 'approved'
            session.commit()
            print(f"✅ Мероприятие {event_id} опубликовано")
            return True
        print(f"❌ Мероприятие {event_id} не найдено")
        return False

async def reject_event(event_id):
    """Отклонить мероприятие"""
    print(f"🔍 ВЫЗОВ reject_event для ID {event_id}")
    with Session() as session:
        event = session.get(Event, event_id)
        if event:
            event.status = 'rejected'
            session.commit()
            print(f"❌ Мероприятие {event_id} отклонено")
            return True
        print(f"❌ Мероприятие {event_id} не найдено")
        return False

# ----- ПРОДВИЖЕНИЕ -----

async def cleanup_expired_promotions():
    """Очистить просроченные продвижения"""
    with Session() as session:
        now = datetime.now()
        expired = session.execute(
            select(PromotedEvent).where(
                and_(
                    PromotedEvent.is_active == True,
                    PromotedEvent.expires_at <= now
                )
            )
        ).scalars().all()
        
        for promo in expired:
            promo.is_active = False
            event = promo.event
            other_active = session.execute(
                select(PromotedEvent).where(
                    and_(
                        PromotedEvent.event_id == event.event_id,
                        PromotedEvent.is_active == True,
                        PromotedEvent.id != promo.id
                    )
                )
            ).first()
            
            if not other_active:
                event.priority = 0
        
        session.commit()
        return len(expired)

# ----- ДРУЗЬЯ -----

async def get_all_users():
    """Получить всех пользователей"""
    print("🔍 ПОЛУЧЕНИЕ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ")
    with Session() as session:
        users = session.execute(select(User)).scalars().all()
        return users

async def add_friend(user_id, friend_id):
    """Добавить подругу"""
    print(f"🔍 ДОБАВЛЕНИЕ ПОДРУГИ: {user_id} -> {friend_id}")
    with Session() as session:
        existing = session.execute(
            select(Friend).where(
                Friend.user_id == user_id,
                Friend.friend_id == friend_id
            )
        ).first()
        
        if existing:
            print(f"❌ Уже в подругах")
            return False
        
        friend = Friend(
            user_id=user_id,
            friend_id=friend_id
        )
        session.add(friend)
        session.commit()
        print(f"✅ Подруга добавлена")
        return True

async def remove_friend(user_id, friend_id):
    """Удалить подругу"""
    print(f"🔍 УДАЛЕНИЕ ПОДРУГИ: {user_id} -> {friend_id}")
    with Session() as session:
        friend = session.execute(
            select(Friend).where(
                Friend.user_id == user_id,
                Friend.friend_id == friend_id
            )
        ).scalar_one_or_none()
        
        if not friend:
            print(f"❌ Не найдена")
            return False
        
        session.delete(friend)
        session.commit()
        print(f"✅ Подруга удалена")
        return True

async def get_friends(user_id):
    """Получить список подруг пользователя"""
    print(f"🔍 ПОЛУЧЕНИЕ ПОДРУГ пользователя {user_id}")
    with Session() as session:
        friends = session.execute(
            select(Friend).where(Friend.user_id == user_id)
        ).scalars().all()
        return friends

async def get_fans(user_id):
    """Получить список тех, кто добавил пользователя в подруги"""
    print(f"🔍 ПОЛУЧЕНИЕ ФАНАТОВ пользователя {user_id}")
    with Session() as session:
        fans = session.execute(
            select(Friend).where(Friend.friend_id == user_id)
        ).scalars().all()
        return fans

async def is_friend(user_id, friend_id):
    """Проверить, является ли пользователь подругой"""
    with Session() as session:
        friend = session.execute(
            select(Friend).where(
                Friend.user_id == user_id,
                Friend.friend_id == friend_id
            )
        ).first()
        return friend is not None

async def is_fan(user_id, fan_id):
    """Проверить, добавил ли пользователь в подруги"""
    with Session() as session:
        fan = session.execute(
            select(Friend).where(
                Friend.user_id == fan_id,
                Friend.friend_id == user_id
            )
        ).first()
        return fan is not None
# ----- УВЕДОМЛЕНИЯ -----

async def save_notification(user_id, event_id, notification_type):
    """Сохранить информацию об отправленном уведомлении"""
    print(f"🔍 СОХРАНЕНИЕ УВЕДОМЛЕНИЯ: пользователь {user_id}, событие {event_id}, тип {notification_type}")
    with Session() as session:
        from .models import NotificationHistory
        notification = NotificationHistory(
            user_id=user_id,
            event_id=event_id,
            notification_type=notification_type
        )
        session.add(notification)
        session.commit()
        return True

async def get_notification_count(user_id, event_id, notification_type, days=7):
    """Получить количество отправленных уведомлений за последние N дней"""
    with Session() as session:
        from .models import NotificationHistory
        from datetime import datetime, timedelta
        
        cutoff = datetime.now() - timedelta(days=days)
        
        count = session.query(NotificationHistory).filter(
            NotificationHistory.user_id == user_id,
            NotificationHistory.event_id == event_id,
            NotificationHistory.notification_type == notification_type,
            NotificationHistory.sent_at >= cutoff
        ).count()
        
        return count

async def get_daily_notification_count(user_id, notification_type):
    """Получить количество уведомлений за сегодня"""
    with Session() as session:
        from .models import NotificationHistory
        from datetime import datetime
        
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        count = session.query(NotificationHistory).filter(
            NotificationHistory.user_id == user_id,
            NotificationHistory.notification_type == notification_type,
            NotificationHistory.sent_at >= today_start
        ).count()
        
        return count