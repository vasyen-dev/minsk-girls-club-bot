from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta
import asyncio

from database.requests import Session, get_user, get_event, save_notification, get_notification_count, get_daily_notification_count
from database.models import Event, EventParticipant, User, Interest, NotificationHistory
from sqlalchemy import select, and_

router = Router()

# Время отправки уведомлений (10:00 утра)
NOTIFICATION_HOUR = 10
NOTIFICATION_MINUTE = 0

async def should_send_notification(user_id, event_id, notification_type, max_daily=3, max_total=2):
    """Проверить, нужно ли отправлять уведомление"""
    # Проверяем дневной лимит
    daily_count = await get_daily_notification_count(user_id, notification_type)
    if daily_count >= max_daily:
        print(f"❌ Дневной лимит ({max_daily}) для пользователя {user_id} исчерпан")
        return False
    
    # Проверяем общий лимит для этого мероприятия
    total_count = await get_notification_count(user_id, event_id, notification_type, days=30)
    if total_count >= max_total:
        print(f"❌ Лимит повторений ({max_total}) для мероприятия {event_id} исчерпан")
        return False
    
    return True

async def wait_until_notification_time():
    """Ждать до времени отправки уведомлений"""
    now = datetime.now()
    target = now.replace(hour=NOTIFICATION_HOUR, minute=NOTIFICATION_MINUTE, second=0, microsecond=0)
    
    # Если уже прошло время сегодня, ждем до завтра
    if now > target:
        target = target + timedelta(days=1)
    
    wait_seconds = (target - now).total_seconds()
    print(f"🕒 Ждем {wait_seconds/3600:.1f} часов до следующей рассылки уведомлений")
    await asyncio.sleep(wait_seconds)

async def check_new_events_for_users(bot: Bot):
    """Отправляет уведомления о новых мероприятиях по интересам (макс 3 в день, не чаще 2 раз на мероприятие)"""
    while True:
        try:
            # Ждем до времени отправки
            await wait_until_notification_time()
            
            print(f"\n🔔 НАЧАЛО РАССЫЛКИ УВЕДОМЛЕНИЙ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
            now = datetime.now()
            
            with Session() as session:
                # Ищем новые мероприятия (созданные за последние 3 дня)
                three_days_ago = now - timedelta(days=3)
                new_events = session.execute(
                    select(Event).where(
                        and_(
                            Event.created_at >= three_days_ago,
                            Event.status == 'approved'
                        )
                    )
                ).scalars().all()
                
                print(f"🔍 Найдено новых мероприятий: {len(new_events)}")
                
                for event in new_events:
                    # Получаем всех пользователей с таким же интересом
                    users_with_interest = session.execute(
                        select(User).join(User.interests).where(Interest.id == event.category_id)
                    ).scalars().all()
                    
                    print(f"📊 Мероприятие '{event.title}': {len(users_with_interest)} потенциальных участниц")
                    
                    event_date = event.event_date.strftime('%d.%m.%Y %H:%M')
                    
                    # Создаем клавиатуру с действиями
                    builder = InlineKeyboardBuilder()
                    builder.button(text="✅ Пойду!", callback_data=f"reg_{event.event_id}")
                    builder.button(text="👤 Организатор", callback_data=f"contact_org_{event.event_id}")
                    builder.button(text="📍 На карте", callback_data=f"event_location_{event.event_id}")
                    if event.chat_link:
                        builder.button(text="💬 Чат мероприятия", url=event.chat_link)
                    builder.adjust(2)
                    
                    sent_count = 0
                    
                    for user in users_with_interest:
                        # Проверяем, нужно ли отправлять уведомление
                        if await should_send_notification(user.user_id, event.event_id, 'new_event'):
                            try:
                                await bot.send_message(
                                    user.user_id,
                                    f"🎉 *Новое мероприятие по твоим интересам!*\n\n"
                                    f"🌸 *{event.title}*\n"
                                    f"📅 {event_date}\n"
                                    f"📍 {event.address}\n"
                                    f"💰 {event.price}\n\n"
                                    f"Хочешь пойти?",
                                    parse_mode="Markdown",
                                    reply_markup=builder.as_markup()
                                )
                                
                                # Сохраняем в историю
                                await save_notification(user.user_id, event.event_id, 'new_event')
                                sent_count += 1
                                print(f"✅ Уведомление отправлено пользователю {user.user_id}")
                                
                            except Exception as e:
                                print(f"❌ Ошибка отправки уведомления пользователю {user.user_id}: {e}")
                    
                    print(f"📨 Для мероприятия '{event.title}' отправлено {sent_count} уведомлений")
            
            print(f"✅ РАССЫЛКА ЗАВЕРШЕНА {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            
        except Exception as e:
            print(f"❌ Ошибка в системе уведомлений о новых событиях: {e}")
            await asyncio.sleep(3600)

async def check_upcoming_events(bot: Bot):
    """Проверяет предстоящие мероприятия и отправляет напоминания (не чаще 1 раза на мероприятие)"""
    while True:
        try:
            now = datetime.now()
            tomorrow = now + timedelta(days=1)
            
            # Ищем мероприятия, которые будут завтра
            with Session() as session:
                upcoming_events = session.execute(
                    select(Event).where(
                        and_(
                            Event.event_date >= tomorrow.replace(hour=0, minute=0, second=0),
                            Event.event_date < tomorrow.replace(hour=23, minute=59, second=59),
                            Event.status == 'approved'
                        )
                    )
                ).scalars().all()
                
                for event in upcoming_events:
                    # Получаем всех участниц
                    participants = session.execute(
                        select(EventParticipant).where(EventParticipant.event_id == event.event_id)
                    ).scalars().all()
                    
                    event_date = event.event_date.strftime('%d.%m.%Y в %H:%M')
                    
                    # Создаем клавиатуру с действиями
                    builder = InlineKeyboardBuilder()
                    builder.button(text="👤 Организатор", callback_data=f"contact_org_{event.event_id}")
                    builder.button(text="📍 На карте", callback_data=f"event_location_{event.event_id}")
                    if event.chat_link:
                        builder.button(text="💬 Чат мероприятия", url=event.chat_link)
                    builder.adjust(2)
                    
                    for participant in participants:
                        # Для напоминаний отправляем только 1 раз
                        count = await get_notification_count(participant.user_id, event.event_id, 'reminder', days=30)
                        if count == 0:
                            try:
                                user = await get_user(participant.user_id)
                                if user and user.is_active:
                                    await bot.send_message(
                                        participant.user_id,
                                        f"🔔 *Напоминание о мероприятии!*\n\n"
                                        f"🌸 *{event.title}*\n"
                                        f"📅 Завтра в {event_date}\n"
                                        f"📍 {event.address}\n\n"
                                        f"Не забудь прийти! Ждём тебя 💗",
                                        parse_mode="Markdown",
                                        reply_markup=builder.as_markup()
                                    )
                                    await save_notification(participant.user_id, event.event_id, 'reminder')
                                    print(f"✅ Напоминание отправлено пользователю {participant.user_id}")
                            except Exception as e:
                                print(f"❌ Ошибка отправки напоминания пользователю {participant.user_id}: {e}")
            
            # Проверяем каждый час
            await asyncio.sleep(3600)
            
        except Exception as e:
            print(f"❌ Ошибка в системе уведомлений: {e}")
            await asyncio.sleep(3600)

async def on_startup_notifications(bot: Bot):
    """Запускает все уведомления при старте бота"""
    # Запускаем проверку новых мероприятий (будет ждать до 10 утра)
    asyncio.create_task(check_new_events_for_users(bot))
    # Запускаем проверку напоминаний (каждый час)
    asyncio.create_task(check_upcoming_events(bot))
    print("🕒 Система уведомлений запущена")

# Добавляем обработчик для кнопки "📍 На карте"
@router.callback_query(F.data.startswith("event_location_"))
async def event_location(callback: CallbackQuery):
    """Показать местоположение мероприятия на карте"""
    try:
        event_id = int(callback.data.split("_")[2])
    except (IndexError, ValueError):
        await callback.answer("❌ Ошибка загрузки", show_alert=True)
        return
    
    event = await get_event(event_id)
    if not event:
        await callback.answer("❌ Мероприятие не найдено", show_alert=True)
        return
    
    # Если есть координаты, отправляем геолокацию
    if event.latitude and event.longitude:
        await callback.message.answer_location(
            latitude=float(event.latitude),
            longitude=float(event.longitude),
            reply_markup=InlineKeyboardBuilder().button(
                text="◀️ Назад к мероприятию", 
                callback_data=f"back_to_event_{event_id}"
            ).as_markup()
        )
    else:
        # Если координат нет, показываем адрес
        await callback.message.answer(
            f"📍 *Адрес мероприятия:*\n\n{event.address}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardBuilder().button(
                text="◀️ Назад к мероприятию", 
                callback_data=f"back_to_event_{event_id}"
            ).as_markup()
        )
    
    await callback.answer()