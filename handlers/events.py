from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from datetime import datetime, timedelta

from database.requests import get_active_events, get_event, get_user, add_participant, remove_participant, get_user_interests, get_event_participants, get_category_name
from database.requests import get_all_interests

router = Router()

user_filters = {}

@router.message(F.text == "🌸 Найти событие")
async def cmd_find_events(message: Message):
    """Начать поиск мероприятий"""
    await show_filters_menu(message)

async def show_filters_menu(message: Message):
    """Показывает меню выбора фильтров"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🎯 По интересам", callback_data="filter_interest")
    builder.button(text="📍 По району", callback_data="filter_district")
    builder.button(text="📅 По дате", callback_data="filter_date")
    builder.button(text="🚫 Сбросить фильтры", callback_data="filter_reset")
    builder.button(text="🔍 Найти", callback_data="filter_apply")
    builder.adjust(2)
    
    user_id = message.from_user.id
    filters = user_filters.get(user_id, {})
    
    filter_text = "🔍 *Поиск мероприятий*\n\n"
    filter_text += f"🎯 Интересы: {filters.get('interest', 'Все')}\n"
    filter_text += f"📍 Район: {filters.get('district', 'Весь Минск')}\n"
    filter_text += f"📅 Дата: {filters.get('date', 'Все')}\n\n"
    filter_text += "Выбери фильтры или нажми «Найти»"
    
    await message.answer(filter_text, parse_mode="Markdown", reply_markup=builder.as_markup())

@router.callback_query(F.data == "filter_interest")
async def filter_interest(callback: CallbackQuery):
    """Выбор фильтра по интересам"""
    interests = await get_all_interests()
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📌 Все интересы", callback_data="interest_all")
    
    categories = {}
    for interest in interests:
        if interest.category not in categories:
            categories[interest.category] = []
        categories[interest.category].append(interest)
    
    for category, cat_interests in categories.items():
        for interest in cat_interests:
            builder.button(text=f"{interest.name}", callback_data=f"interest_{interest.id}")
    
    builder.button(text="◀️ Назад", callback_data="back_to_filters")
    builder.adjust(2)
    
    await callback.message.edit_text(
        "🎯 *Выбери интерес*",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("interest_"))
async def interest_selected(callback: CallbackQuery):
    """Выбран конкретный интерес"""
    user_id = callback.from_user.id
    
    if callback.data == "interest_all":
        if user_id in user_filters:
            user_filters[user_id].pop('interest', None)
            user_filters[user_id].pop('interest_id', None)
        else:
            user_filters[user_id] = {}
    else:
        interest_id = int(callback.data.split("_")[1])
        interests = await get_all_interests()
        interest_name = next((i.name for i in interests if i.id == interest_id), "Неизвестно")
        
        if user_id not in user_filters:
            user_filters[user_id] = {}
        user_filters[user_id]['interest'] = interest_name
        user_filters[user_id]['interest_id'] = interest_id
    
    await show_filters_menu(callback.message)
    await callback.answer()

@router.callback_query(F.data == "filter_district")
async def filter_district(callback: CallbackQuery):
    """Выбор фильтра по району"""
    from handlers.registration import MINSK_DISTRICTS
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📍 Весь Минск", callback_data="district_all")
    
    for district in MINSK_DISTRICTS:
        builder.button(text=district, callback_data=f"district_{district}")
    
    builder.button(text="◀️ Назад", callback_data="back_to_filters")
    builder.adjust(2)
    
    await callback.message.edit_text(
        "📍 *Выбери район*",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("district_"))
async def district_selected(callback: CallbackQuery):
    """Выбран конкретный район"""
    user_id = callback.from_user.id
    
    if callback.data == "district_all":
        if user_id in user_filters:
            user_filters[user_id].pop('district', None)
    else:
        district = callback.data.split("_")[1]
        if user_id not in user_filters:
            user_filters[user_id] = {}
        user_filters[user_id]['district'] = district
    
    await show_filters_menu(callback.message)
    await callback.answer()

@router.callback_query(F.data == "filter_date")
async def filter_date(callback: CallbackQuery):
    """Выбор фильтра по дате"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Все даты", callback_data="date_all")
    builder.button(text="📅 Сегодня", callback_data="date_today")
    builder.button(text="📅 Завтра", callback_data="date_tomorrow")
    builder.button(text="📅 Эта неделя", callback_data="date_week")
    builder.button(text="📅 Эти выходные", callback_data="date_weekend")
    builder.button(text="◀️ Назад", callback_data="back_to_filters")
    builder.adjust(2)
    
    await callback.message.edit_text(
        "📅 *Выбери дату*",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("date_"))
async def date_selected(callback: CallbackQuery):
    """Выбрана конкретная дата"""
    user_id = callback.from_user.id
    date_option = callback.data.split("_")[1]
    
    date_names = {
        "all": "Все даты",
        "today": "Сегодня",
        "tomorrow": "Завтра",
        "week": "Эта неделя",
        "weekend": "Выходные"
    }
    
    if date_option == "all":
        if user_id in user_filters:
            user_filters[user_id].pop('date', None)
            user_filters[user_id].pop('date_option', None)
    else:
        if user_id not in user_filters:
            user_filters[user_id] = {}
        user_filters[user_id]['date'] = date_names.get(date_option, "Неизвестно")
        user_filters[user_id]['date_option'] = date_option
    
    await show_filters_menu(callback.message)
    await callback.answer()

@router.callback_query(F.data == "filter_reset")
async def filter_reset(callback: CallbackQuery):
    """Сбросить все фильтры"""
    user_id = callback.from_user.id
    if user_id in user_filters:
        user_filters[user_id] = {}
    
    await show_filters_menu(callback.message)
    await callback.answer()

@router.callback_query(F.data == "filter_apply")
async def filter_apply(callback: CallbackQuery):
    """Применить фильтры и показать мероприятия"""
    user_id = callback.from_user.id
    filters = user_filters.get(user_id, {})
    
    events = await get_filtered_events(filters)
    
    if not events:
        await callback.message.edit_text(
            "😔 По выбранным фильтрам ничего не найдено\n\n"
            "Попробуй изменить фильтры или создать своё мероприятие!",
            reply_markup=InlineKeyboardBuilder().button(
                text="◀️ Назад к фильтрам", callback_data="back_to_filters"
            ).as_markup()
        )
        await callback.answer()
        return
    
    if user_id not in user_filters:
        user_filters[user_id] = {}
    user_filters[user_id]['event_list'] = [e.event_id for e in events]
    user_filters[user_id]['current_index'] = 0
    
    await callback.message.delete()
    await show_event(callback.message, user_id, 0)
    await callback.answer()

async def show_event(message: Message, user_id: int, index: int):
    """Показать мероприятие по индексу"""
    filters = user_filters.get(user_id, {})
    event_ids = filters.get('event_list', [])
    
    if not event_ids:
        await message.answer(
            "😔 Список мероприятий пуст",
            reply_markup=InlineKeyboardBuilder().button(
                text="◀️ Назад к фильтрам", callback_data="back_to_filters"
            ).as_markup()
        )
        return
    
    if index < 0:
        index = 0
    if index >= len(event_ids):
        index = len(event_ids) - 1
    
    filters['current_index'] = index
    
    event_id = event_ids[index]
    event = await get_event(event_id)
    
    if not event:
        event_ids.pop(index)
        filters['event_list'] = event_ids
        if event_ids:
            await show_event(message, user_id, min(index, len(event_ids)-1))
        else:
            await message.answer(
                "😔 Мероприятия не найдены",
                reply_markup=InlineKeyboardBuilder().button(
                    text="◀️ Назад к фильтрам", callback_data="back_to_filters"
                ).as_markup()
            )
        return
    
    organizer = await get_user(event.creator_id)
    organizer_name = organizer.name if organizer else "Неизвестно"
    
    participants = await get_event_participants(event_id)
    participant_ids = [p.user_id for p in participants]
    
    is_participant = user_id in participant_ids
    
    event_date = event.event_date.strftime('%d.%m.%Y %H:%M')
    participants_count = len(participants)
    category_name = await get_category_name(event.category_id)
    
    text = (
        f"🌸 *{event.title}*\n\n"
        f"📝 {event.description or 'Нет описания'}\n\n"
        f"📍 {event.address}\n"
        f"🕒 {event_date}\n"
        f"👥 Участниц: {participants_count}/{event.max_participants if event.max_participants > 0 else '∞'}\n"
        f"💰 {event.price}\n"
        f"👤 Организатор: {organizer_name}\n\n"
        f"📊 Всего в списке: {len(event_ids)} мероприятий"
    )
    
    builder = InlineKeyboardBuilder()
    
    if is_participant:
        builder.button(text="❌ Отменить запись", callback_data=f"unreg_{event_id}")
    else:
        if event.max_participants == 0 or participants_count < event.max_participants:
            builder.button(text="✅ Пойду!", callback_data=f"reg_{event_id}")
        else:
            builder.button(text="😔 Мест нет", callback_data="no_seats")
    
    builder.button(text="👤 Связаться", callback_data=f"contact_org_{event_id}")
    
    # Кнопка чата мероприятия, если есть ссылка
    if event.chat_link:
        builder.button(text="💬 Чат мероприятия", url=event.chat_link)
    
    nav_builder = InlineKeyboardBuilder()
    if index > 0:
        nav_builder.button(text="◀️", callback_data="prev_event")
    if index < len(event_ids) - 1:
        nav_builder.button(text="▶️", callback_data="next_event")
    
    if nav_builder.buttons:
        builder.attach(nav_builder)
    
    builder.button(text="🏠 В меню", callback_data="back_to_filters")
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

@router.callback_query(F.data == "prev_event")
async def prev_event(callback: CallbackQuery):
    """Предыдущее мероприятие"""
    user_id = callback.from_user.id
    filters = user_filters.get(user_id, {})
    current_index = filters.get('current_index', 0)
    
    if current_index > 0:
        filters['current_index'] = current_index - 1
        await callback.message.delete()
        await show_event(callback.message, user_id, current_index - 1)
    else:
        await callback.answer("Это первое мероприятие", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data == "next_event")
async def next_event(callback: CallbackQuery):
    """Следующее мероприятие"""
    user_id = callback.from_user.id
    filters = user_filters.get(user_id, {})
    current_index = filters.get('current_index', 0)
    event_ids = filters.get('event_list', [])
    
    if current_index < len(event_ids) - 1:
        filters['current_index'] = current_index + 1
        await callback.message.delete()
        await show_event(callback.message, user_id, current_index + 1)
    else:
        await callback.answer("Это последнее мероприятие", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data.startswith("reg_"))
async def register_for_event(callback: CallbackQuery):
    """Записаться на мероприятие"""
    try:
        event_id = int(callback.data.split("_")[1])
        user_id = callback.from_user.id
        
        result = await add_participant(event_id, user_id)
        
        if result:
            event = await get_event(event_id)
            
            # Если есть чат, отправляем ссылку
            if event and event.chat_link:
                await callback.message.answer(
                    f"💬 *Чат мероприятия*\n\n"
                    f"Организатор создала чат для обсуждения!\n"
                    f"Присоединяйся: {event.chat_link}",
                    parse_mode="Markdown"
                )
            
            await callback.answer("✅ Ты записалась!", show_alert=False)
            
            filters = user_filters.get(user_id, {})
            current_index = filters.get('current_index', 0)
            await callback.message.delete()
            await show_event(callback.message, user_id, current_index)
        else:
            await callback.answer("❌ Ошибка записи", show_alert=True)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)

@router.callback_query(F.data.startswith("unreg_"))
async def unregister_from_event(callback: CallbackQuery):
    """Отменить запись"""
    try:
        event_id = int(callback.data.split("_")[1])
        user_id = callback.from_user.id
        
        result = await remove_participant(event_id, user_id)
        
        if result:
            await callback.answer("❌ Запись отменена", show_alert=False)
            
            filters = user_filters.get(user_id, {})
            current_index = filters.get('current_index', 0)
            await callback.message.delete()
            await show_event(callback.message, user_id, current_index)
        else:
            await callback.answer("❌ Ошибка отмены", show_alert=True)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)

@router.callback_query(F.data.startswith("contact_org_"))
async def contact_organizer(callback: CallbackQuery):
    """Показать контакты организатора"""
    try:
        event_id = int(callback.data.split("_")[2])
    except (IndexError, ValueError):
        await callback.answer("❌ Ошибка загрузки", show_alert=True)
        return
    
    event = await get_event(event_id)
    if not event:
        await callback.answer("❌ Мероприятие не найдено", show_alert=True)
        return
    
    organizer = await get_user(event.creator_id)
    if not organizer:
        await callback.answer("❌ Организатор не найден", show_alert=True)
        return
    
    contact_text = f"👤 *Организатор:* {organizer.name}\n\n"
    
    if organizer.username:
        contact_text += f"📱 Telegram: @{organizer.username}\n"
    if organizer.instagram:
        contact_text += f"📸 Instagram: @{organizer.instagram}\n"
    if organizer.bio:
        contact_text += f"\n📝 О себе: {organizer.bio}\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад к мероприятию", callback_data=f"back_to_event_{event_id}")
    
    await callback.message.answer(
        contact_text,
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("back_to_event_"))
async def back_to_event_from_contact(callback: CallbackQuery):
    """Вернуться к мероприятию после просмотра контактов"""
    try:
        event_id = int(callback.data.split("_")[3])
    except (IndexError, ValueError):
        await callback.answer("❌ Ошибка навигации", show_alert=True)
        return
    
    user_id = callback.from_user.id
    filters = user_filters.get(user_id, {})
    current_index = filters.get('current_index', 0)
    
    await callback.message.delete()
    await show_event(callback.message, user_id, current_index)
    await callback.answer()

@router.callback_query(F.data == "back_to_filters")
async def back_to_filters(callback: CallbackQuery):
    """Вернуться к фильтрам"""
    await callback.message.delete()
    await show_filters_menu(callback.message)
    await callback.answer()

@router.callback_query(F.data == "no_seats")
async def no_seats(callback: CallbackQuery):
    """Нет мест"""
    await callback.answer("😔 Все места заняты", show_alert=True)

async def get_filtered_events(filters):
    """Получить мероприятия с учётом фильтров"""
    category_id = filters.get('interest_id')
    district = filters.get('district')
    
    events = await get_active_events(
        category=category_id,
        district=district
    )
    
    date_option = filters.get('date_option')
    if date_option and date_option != 'all':
        now = datetime.now()
        if date_option == 'today':
            events = [e for e in events if e.event_date.date() == now.date()]
        elif date_option == 'tomorrow':
            tomorrow = now.date() + timedelta(days=1)
            events = [e for e in events if e.event_date.date() == tomorrow]
    
    return events