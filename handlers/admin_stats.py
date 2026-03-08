from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta

from database.requests import Session, get_user, get_user_interests, get_user_events, get_user_created_events
from database.models import User, Event, EventParticipant, Interest
from config import ADMIN_IDS
from sqlalchemy import select, func

router = Router()

# Состояния для рассылки
class BroadcastStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_confirm = State()

@router.message(Command("stats"), F.from_user.id.in_(ADMIN_IDS))
async def cmd_stats(message: Message):
    """Показать статистику бота (только для админов)"""
    print(f"\n🔍 ===== ЗАПРОС СТАТИСТИКИ ОТ АДМИНА {message.from_user.id} =====")
    
    with Session() as session:
        # Общая статистика
        total_users = session.query(User).count()
        total_events = session.query(Event).count()
        total_participations = session.query(EventParticipant).count()
        
        # Статистика по статусам мероприятий
        pending_events = session.query(Event).filter(Event.status == 'pending').count()
        approved_events = session.query(Event).filter(Event.status == 'approved').count()
        completed_events = session.query(Event).filter(Event.status == 'completed').count()
        rejected_events = session.query(Event).filter(Event.status == 'rejected').count()
        
        # Статистика за сегодня
        today = datetime.now().date()
        today_start = datetime(today.year, today.month, today.day)
        
        new_users_today = session.query(User).filter(User.registered_at >= today_start).count()
        new_events_today = session.query(Event).filter(Event.created_at >= today_start).count()
        
        # Активные мероприятия (ближайшие)
        upcoming_events = session.query(Event).filter(
            Event.event_date >= datetime.now(),
            Event.status == 'approved'
        ).count()
        
        # Популярные интересы
        interest_stats = session.query(
            Interest.name, 
            func.count(User.user_id).label('user_count')
        ).join(Interest.users).group_by(Interest.id).order_by(func.count(User.user_id).desc()).limit(5).all()
        
        # Формируем текст статистики
        stats_text = (
            f"📊 *Статистика бота*\n\n"
            f"👥 *Пользователи:*\n"
            f"• Всего: {total_users}\n"
            f"• Новых сегодня: {new_users_today}\n\n"
            
            f"📅 *Мероприятия:*\n"
            f"• Всего: {total_events}\n"
            f"• Новых сегодня: {new_events_today}\n"
            f"• На модерации: {pending_events}\n"
            f"• Опубликовано: {approved_events}\n"
            f"• Завершено: {completed_events}\n"
            f"• Отклонено: {rejected_events}\n"
            f"• Предстоит: {upcoming_events}\n\n"
            
            f"📝 *Записи:*\n"
            f"• Всего записей: {total_participations}\n\n"
            
            f"🔥 *Топ интересов:*\n"
        )
        
        for name, count in interest_stats:
            stats_text += f"• {name}: {count} девушек\n"
        
        await message.answer(stats_text, parse_mode="Markdown")

@router.message(Command("broadcast"), F.from_user.id.in_(ADMIN_IDS))
async def cmd_broadcast(message: Message, state: FSMContext):
    """Начать рассылку сообщения всем пользователям"""
    await state.set_state(BroadcastStates.waiting_for_message)
    await message.answer(
        "📢 *Рассылка*\n\n"
        "Отправь сообщение, которое нужно разослать всем пользователям:\n"
        "(можно текст, фото, видео)\n\n"
        "Для отмены напиши /cancel",
        parse_mode="Markdown"
    )

@router.message(BroadcastStates.waiting_for_message)
async def process_broadcast_message(message: Message, state: FSMContext):
    """Получить сообщение для рассылки"""
    # Сохраняем сообщение в состоянии
    await state.update_data(
        message_id=message.message_id,
        from_chat_id=message.chat.id
    )
    await state.set_state(BroadcastStates.waiting_for_confirm)
    
    # Показываем предпросмотр и запрашиваем подтверждение
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Отправить", callback_data="broadcast_confirm")
    builder.button(text="❌ Отмена", callback_data="broadcast_cancel")
    builder.adjust(2)
    
    await message.answer(
        "📢 *Подтверждение рассылки*\n\n"
        "Вот так сообщение увидят пользователи. Отправляем?",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )
    
    # Пересылаем сообщение для предпросмотра
    await message.copy_to(message.chat.id)

@router.callback_query(F.data == "broadcast_confirm")
async def broadcast_confirm(callback: CallbackQuery, state: FSMContext):
    """Подтвердить рассылку"""
    data = await state.get_data()
    message_id = data.get('message_id')
    from_chat_id = data.get('from_chat_id')
    
    await callback.message.edit_text("📢 Рассылка началась...")
    
    # Получаем всех пользователей
    with Session() as session:
        users = session.execute(select(User)).scalars().all()
        
        success = 0
        failed = 0
        
        for user in users:
            try:
                await callback.bot.copy_message(
                    chat_id=user.user_id,
                    from_chat_id=from_chat_id,
                    message_id=message_id
                )
                success += 1
            except Exception as e:
                print(f"❌ Ошибка отправки пользователю {user.user_id}: {e}")
                failed += 1
        
        await callback.message.edit_text(
            f"📢 *Рассылка завершена*\n\n"
            f"✅ Успешно: {success}\n"
            f"❌ Ошибок: {failed}",
            parse_mode="Markdown"
        )
    
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "broadcast_cancel")
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    """Отменить рассылку"""
    await state.clear()
    await callback.message.edit_text("❌ Рассылка отменена")
    await callback.answer()

@router.message(Command("user"), F.from_user.id.in_(ADMIN_IDS))
async def cmd_user_info(message: Message):
    """Показать информацию о пользователе по ID"""
    args = message.text.split()
    
    if len(args) < 2:
        await message.answer("❌ Укажи ID пользователя: /user 123456789")
        return
    
    try:
        user_id = int(args[1])
    except ValueError:
        await message.answer("❌ ID должен быть числом")
        return
    
    user = await get_user(user_id)
    if not user:
        await message.answer(f"❌ Пользователь с ID {user_id} не найден")
        return
    
    interests = await get_user_interests(user_id)
    interests_text = ", ".join([i.name for i in interests]) if interests else "Не выбраны"
    
    registrations = await get_user_events(user_id)
    created = await get_user_created_events(user_id)
    
    text = (
        f"👤 *Информация о пользователе*\n\n"
        f"🆔 ID: `{user.user_id}`\n"
        f"👤 Имя: {user.name}\n"
        f"🎂 Возраст: {user.age}\n"
        f"📍 Район: {user.district}\n"
        f"📝 О себе: {user.bio or 'Не указано'}\n"
        f"📸 Instagram: {user.instagram or 'Не указан'}\n"
        f"📱 Telegram: @{user.username or 'не указан'}\n"
        f"📅 Зарегистрирована: {user.registered_at.strftime('%d.%m.%Y')}\n\n"
        f"🎯 Интересы: {interests_text}\n"
        f"📝 Записей: {len(registrations)}\n"
        f"✨ Создано встреч: {len(created)}"
    )
    
    builder = InlineKeyboardBuilder()
    if user.username:
        builder.button(text="📱 Написать в Telegram", url=f"https://t.me/{user.username}")
    elif user.instagram:
        builder.button(text="📸 Написать в Instagram", url=f"https://instagram.com/{user.instagram}")
    builder.adjust(1)
    
    if user.photo_file_id:
        await message.answer_photo(
            photo=user.photo_file_id,
            caption=text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
    else:
        await message.answer(
            text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
@router.message(Command("add_interests"), F.from_user.id.in_(ADMIN_IDS))
async def cmd_add_interests(message: Message):
    """Добавить интересы в базу данных (только для админов)"""
    from database.requests import Session
    from database.models import Interest
    
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
        # Проверяем, есть ли уже интересы
        if session.query(Interest).count() > 0:
            await message.answer("❌ Интересы уже есть в базе")
            return
        
        for item in interests_data:
            interest = Interest(name=item["name"], category=item["category"])
            session.add(interest)
        session.commit()
        
        await message.answer(f"✅ Добавлено {len(interests_data)} интересов!")