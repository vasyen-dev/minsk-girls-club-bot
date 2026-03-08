from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime

from database.requests import get_user_events, get_user_created_events, get_event_participants, get_event, get_category_name, get_user
from handlers.events import contact_organizer, user_filters

router = Router()

@router.message(F.text == "📅 Мои планы")
async def cmd_my_plans(message: Message):
    """Показать меню моих планов"""
    user_id = message.from_user.id
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Мои записи", callback_data="my_registrations")
    builder.button(text="✨ Мои встречи", callback_data="my_created")
    builder.adjust(1)
    
    await message.answer(
        "📅 *Мои планы*\n\n"
        "Выбери, что хочешь посмотреть:",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data == "my_registrations")
async def my_registrations(callback: CallbackQuery):
    """Показать мероприятия, на которые записалась"""
    user_id = callback.from_user.id
    
    # Получаем мероприятия, на которые пользователь записан
    events = await get_user_events(user_id)
    
    if not events:
        await callback.message.edit_text(
            "📝 У тебя пока нет записей на мероприятия\n\n"
            "Нажми «🌸 Найти событие», чтобы выбрать встречу!",
            reply_markup=InlineKeyboardBuilder().button(
                text="◀️ Назад", callback_data="back_to_plans"
            ).as_markup()
        )
        await callback.answer()
        return
    
    # Сохраняем список мероприятий в кэш для навигации
    user_filters[user_id] = {
        'event_list': [e.event_id for e in events],
        'current_index': 0,
        'source': 'registrations'
    }
    
    await callback.message.delete()
    await show_plan_event(callback.message, user_id, 0, "registrations")
    await callback.answer()

@router.callback_query(F.data == "my_created")
async def my_created(callback: CallbackQuery):
    """Показать созданные мероприятия"""
    user_id = callback.from_user.id
    
    # Получаем мероприятия, созданные пользователем
    events = await get_user_created_events(user_id)
    
    if not events:
        await callback.message.edit_text(
            "✨ Ты ещё не создала ни одной встречи\n\n"
            "Нажми «✨ Создать встречу», чтобы организовать мероприятие!",
            reply_markup=InlineKeyboardBuilder().button(
                text="◀️ Назад", callback_data="back_to_plans"
            ).as_markup()
        )
        await callback.answer()
        return
    
    # Сохраняем список мероприятий в кэш для навигации
    user_filters[user_id] = {
        'event_list': [e.event_id for e in events],
        'current_index': 0,
        'source': 'created'
    }
    
    await callback.message.delete()
    await show_plan_event(callback.message, user_id, 0, "created")
    await callback.answer()

async def show_plan_event(message: Message, user_id: int, index: int, source: str):
    """Показать мероприятие из списка планов"""
    filters = user_filters.get(user_id, {})
    event_ids = filters.get('event_list', [])
    
    if not event_ids or index >= len(event_ids):
        await message.answer("😔 Список пуст")
        return
    
    event_id = event_ids[index]
    event = await get_event(event_id)
    
    if not event:
        await message.answer("❌ Ошибка загрузки мероприятия")
        return
    
    # Получаем данные организатора
    organizer = await get_user(event.creator_id)
    organizer_name = organizer.name if organizer else "Неизвестно"
    
    # Получаем участников
    participants = await get_event_participants(event_id)
    participants_count = len(participants)
    
    # Получаем название категории
    category_name = await get_category_name(event.category_id)
    
    # Форматируем дату
    event_date = event.event_date.strftime('%d.%m.%Y %H:%M')
    
    # Статус мероприятия
    now = datetime.now()
    if event.event_date < now:
        status = "⏳ Прошло"
    else:
        status = "🔥 Актуально"
    
    # Специальный текст в зависимости от источника
    if source == "created":
        header = "✨ *Твоя встреча*\n\n"
    else:
        header = "📝 *Твоя запись*\n\n"
    
    text = (
        header +
        f"*Название:* {event.title}\n"
        f"*Категория:* {category_name}\n"
        f"*Описание:* {event.description or 'Нет описания'}\n"
        f"📍 {event.address}\n"
        f"🕒 {event_date}\n"
        f"👥 Участниц: {participants_count}/{event.max_participants if event.max_participants > 0 else '∞'}\n"
        f"💰 {event.price}\n"
        f"👤 Организатор: {organizer_name}\n"
        f"📊 Статус: {status}\n\n"
    )
    
    builder = InlineKeyboardBuilder()
    
    # Кнопки для создателя
    if source == "created":
        builder.button(text="📊 Участницы", callback_data=f"show_participants_{event_id}")
        if event.status == 'pending':
            builder.button(text="⏳ На модерации", callback_data="pending_info")
    
    # Кнопка отмены записи (для записей)
    if source == "registrations" and event.event_date > now:
        builder.button(text="❌ Отменить запись", callback_data=f"cancel_plan_{event_id}")
    
    # Кнопка связи с организатором
    builder.button(text="👤 Организатор", callback_data=f"contact_org_{event_id}")
    
    # Кнопка чата мероприятия (если есть)
    if event.chat_link:
        builder.button(text="💬 Чат мероприятия", url=event.chat_link)
    
    # Навигация
    nav_builder = InlineKeyboardBuilder()
    if index > 0:
        nav_builder.button(text="◀️", callback_data=f"prev_plan_{source}")
    if index < len(event_ids) - 1:
        nav_builder.button(text="▶️", callback_data=f"next_plan_{source}")
    
    if nav_builder.buttons:
        builder.attach(nav_builder)
    
    builder.button(text="🏠 В меню", callback_data="back_to_plans")
    builder.adjust(2)
    
    if event.photo_file_id:
        await message.answer_photo(
            photo=event.photo_file_id,
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

@router.callback_query(F.data.startswith("prev_plan_"))
async def prev_plan_event(callback: CallbackQuery):
    """Предыдущее мероприятие в планах"""
    source = callback.data.split("_")[2]  # registrations или created
    user_id = callback.from_user.id
    
    filters = user_filters.get(user_id, {})
    current_index = filters.get('current_index', 0)
    
    if current_index > 0:
        filters['current_index'] = current_index - 1
        await callback.message.delete()
        await show_plan_event(callback.message, user_id, current_index - 1, source)
    
    await callback.answer()

@router.callback_query(F.data.startswith("next_plan_"))
async def next_plan_event(callback: CallbackQuery):
    """Следующее мероприятие в планах"""
    source = callback.data.split("_")[2]  # registrations или created
    user_id = callback.from_user.id
    
    filters = user_filters.get(user_id, {})
    current_index = filters.get('current_index', 0)
    event_ids = filters.get('event_list', [])
    
    if current_index < len(event_ids) - 1:
        filters['current_index'] = current_index + 1
        await callback.message.delete()
        await show_plan_event(callback.message, user_id, current_index + 1, source)
    
    await callback.answer()

@router.callback_query(F.data.startswith("cancel_plan_"))
async def cancel_plan_registration(callback: CallbackQuery):
    """Отменить запись из планов"""
    event_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    from database.requests import remove_participant
    result = await remove_participant(event_id, user_id)
    
    if result:
        await callback.answer("❌ Запись отменена", show_alert=True)
        # Возвращаемся к списку записей
        await my_registrations(callback)
    else:
        await callback.answer("❌ Ошибка отмены", show_alert=True)

@router.callback_query(F.data.startswith("show_participants_"))
async def show_participants(callback: CallbackQuery):
    """Показать список участниц мероприятия"""
    event_id = int(callback.data.split("_")[2])
    
    from database.requests import get_event_participants, get_user
    participants = await get_event_participants(event_id)
    
    if not participants:
        await callback.answer("😔 Пока никто не записался", show_alert=True)
        return
    
    text = "👥 *Участницы:*\n\n"
    for i, p in enumerate(participants, 1):
        user = await get_user(p.user_id)
        if user:
            name = user.name
            insta = f" (@{user.instagram})" if user.instagram else ""
            text += f"{i}. {name}{insta}\n"
    
    await callback.message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardBuilder().button(
            text="◀️ Назад", callback_data=f"back_to_event_{event_id}"
        ).as_markup()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("back_to_event_"))
async def back_to_event(callback: CallbackQuery):
    """Вернуться к мероприятию из списка участниц"""
    event_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    filters = user_filters.get(user_id, {})
    source = filters.get('source', 'registrations')
    current_index = filters.get('current_index', 0)
    
    await callback.message.delete()
    await show_plan_event(callback.message, user_id, current_index, source)
    await callback.answer()

@router.callback_query(F.data == "pending_info")
async def pending_info(callback: CallbackQuery):
    """Информация о модерации"""
    await callback.answer(
        "⏳ Мероприятие на модерации. Обычно проверка занимает до 2 часов.",
        show_alert=True
    )

@router.callback_query(F.data == "back_to_plans")
async def back_to_plans(callback: CallbackQuery):
    """Вернуться в меню планов"""
    await callback.message.delete()
    await cmd_my_plans(callback.message)
    await callback.answer()