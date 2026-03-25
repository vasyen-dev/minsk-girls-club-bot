from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from datetime import datetime

from database.requests import get_user, get_all_interests, add_event
from handlers.registration import show_main_menu
from handlers.calendar import create_calendar, create_hour_keyboard, create_minute_keyboard

router = Router()

class CreateEventStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_category = State()
    waiting_for_photo = State()
    waiting_for_location = State()
    waiting_for_date = State()
    waiting_for_price = State()
    waiting_for_participants = State()
    waiting_for_chat_link = State()
    selected_date = State()
    selected_hour = State()

def get_navigation_keyboard(show_back=True, show_cancel=True):
    builder = ReplyKeyboardBuilder()
    if show_back:
        builder.button(text="◀️ Назад")
    if show_cancel:
        builder.button(text="❌ Отмена")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_skip_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="◀️ Назад")
    builder.button(text="⏩ Пропустить")
    builder.button(text="❌ Отмена")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

async def get_selected_date_str(state: FSMContext):
    """Получить строку с выбранной датой"""
    data = await state.get_data()
    selected_date = data.get('selected_date')
    if selected_date:
        return selected_date.strftime('%d.%m.%Y')
    return "не выбрана"

@router.message(F.text == "✨ Создать встречу")
async def cmd_create_event(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = await get_user(user_id)
    
    if not user:
        await message.answer("❌ Сначала нужно зарегистрироваться! Напиши /start")
        return
    
    await state.set_state(CreateEventStates.waiting_for_title)
    await message.answer(
        "🌸 *Создание новой встречи*\n\n"
        "Давай придумаем название! Как назовём мероприятие?",
        parse_mode="Markdown",
        reply_markup=get_navigation_keyboard(show_back=False, show_cancel=True)
    )

@router.message(CreateEventStates.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    print("📝 ПОЛУЧИЛИ НАЗВАНИЕ")
    
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание отменено", reply_markup=None)
        await show_main_menu(message)
        return
    
    title = message.text.strip()
    if len(title) < 3 or len(title) > 100:
        await message.answer("Название должно быть от 3 до 100 символов:")
        return
    
    await state.update_data(title=title)
    await state.set_state(CreateEventStates.waiting_for_description)
    await message.answer(
        f"Отлично! Название: *{title}*\n\n"
        "Теперь напиши описание мероприятия 📝",
        parse_mode="Markdown",
        reply_markup=get_navigation_keyboard(show_back=True, show_cancel=True)
    )

@router.message(CreateEventStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    print("📝 ПОЛУЧИЛИ ОПИСАНИЕ")
    
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание отменено", reply_markup=None)
        await show_main_menu(message)
        return
    elif message.text == "◀️ Назад":
        await state.set_state(CreateEventStates.waiting_for_title)
        await message.answer("🌸 Введи название:", reply_markup=get_navigation_keyboard(show_back=False, show_cancel=True))
        return
    
    description = message.text.strip()
    if len(description) < 10:
        await message.answer("Описание должно быть не менее 10 символов:")
        return
    if len(description) > 1000:
        await message.answer("Описание слишком длинное (максимум 1000 символов):")
        return
    
    await state.update_data(description=description)
    await state.set_state(CreateEventStates.waiting_for_category)
    await show_categories(message, state)

async def show_categories(message: Message, state: FSMContext):
    from handlers.categories import EVENT_CATEGORIES
    
    builder = InlineKeyboardBuilder()
    for category in EVENT_CATEGORIES:
        builder.button(text=category, callback_data=f"cat_{category}")
    builder.button(text="◀️ Назад", callback_data="back_to_description")
    builder.button(text="❌ Отмена", callback_data="cancel_create")
    builder.adjust(2)
    
    await message.answer("Выбери категорию мероприятия:", reply_markup=builder.as_markup())

@router.callback_query(CreateEventStates.waiting_for_category, F.data.startswith("cat_"))
async def process_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data[4:]
    await state.update_data(category=category)
    await state.set_state(CreateEventStates.waiting_for_photo)
    
    await callback.message.edit_text(
        f"Категория: *{category}*\n\n"
        "Теперь загрузи фото 📸\n(можно пропустить)",
        parse_mode="Markdown"
    )
    await callback.message.answer("👇 Выбери действие:", reply_markup=get_skip_keyboard())
    await callback.answer()

@router.callback_query(F.data == "back_to_description")
async def back_to_description(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateEventStates.waiting_for_description)
    await callback.message.delete()
    await callback.message.answer("📝 Напиши описание:", reply_markup=get_navigation_keyboard(show_back=True, show_cancel=True))
    await callback.answer()

@router.callback_query(F.data == "cancel_create")
async def cancel_create_callback(callback: CallbackQuery, state: FSMContext):
    """Отмена создания"""
    await state.clear()
    
    if callback.message.text:
        await callback.message.edit_text("❌ Создание отменено")
    else:
        await callback.message.delete()
        await callback.message.answer("❌ Создание отменено")
    
    await show_main_menu(callback.message)
    await callback.answer()

@router.message(CreateEventStates.waiting_for_photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание отменено", reply_markup=None)
        await show_main_menu(message)
        return
    elif message.text == "◀️ Назад":
        await state.set_state(CreateEventStates.waiting_for_category)
        await show_categories(message, state)
        return
    
    photo_file_id = message.photo[-1].file_id
    await state.update_data(photo_file_id=photo_file_id)
    await message.answer("✅ Фото загружено!")
    await state.set_state(CreateEventStates.waiting_for_location)
    await ask_location(message, state)

@router.message(CreateEventStates.waiting_for_photo)
async def process_photo_skip(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    
    if text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание отменено", reply_markup=None)
        await show_main_menu(message)
        return
    elif text == "◀️ Назад":
        await state.set_state(CreateEventStates.waiting_for_category)
        await show_categories(message, state)
        return
    elif text == "⏩ Пропустить":
        await state.update_data(photo_file_id=None)
        await state.set_state(CreateEventStates.waiting_for_location)
        await ask_location(message, state)
    else:
        await message.answer("Отправь фото или нажми «Пропустить»")

async def ask_location(message: Message, state: FSMContext):
    await message.answer(
        "📍 Где пройдёт встреча?\n\n"
        "Отправь геолокацию или напиши адрес",
        reply_markup=get_navigation_keyboard(show_back=True, show_cancel=True)
    )

@router.message(CreateEventStates.waiting_for_location, F.location)
async def process_location(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание отменено", reply_markup=None)
        await show_main_menu(message)
        return
    elif message.text == "◀️ Назад":
        await state.set_state(CreateEventStates.waiting_for_photo)
        await message.answer("📸 Загрузи фото:", reply_markup=get_skip_keyboard())
        return
    
    latitude = message.location.latitude
    longitude = message.location.longitude
    await state.update_data(latitude=str(latitude), longitude=str(longitude), address="📍 По геолокации")
    await state.set_state(CreateEventStates.waiting_for_date)
    await ask_date(message, state)

@router.message(CreateEventStates.waiting_for_location)
async def process_address(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание отменено", reply_markup=None)
        await show_main_menu(message)
        return
    elif message.text == "◀️ Назад":
        await state.set_state(CreateEventStates.waiting_for_photo)
        await message.answer("📸 Загрузи фото:", reply_markup=get_skip_keyboard())
        return
    
    address = message.text.strip()
    await state.update_data(address=address, latitude=None, longitude=None)
    await state.set_state(CreateEventStates.waiting_for_date)
    await ask_date(message, state)

async def ask_date(message: Message, state: FSMContext):
    """Спрашиваем дату с календарем"""
    print("📅 СПРАШИВАЕМ ДАТУ")
    now = datetime.now()
    await message.answer(
        "📅 *Выбери дату мероприятия*",
        parse_mode="Markdown",
        reply_markup=create_calendar(now.year, now.month)
    )

@router.callback_query(CreateEventStates.waiting_for_date, F.data.startswith("date_"))
async def process_date_selected(callback: CallbackQuery, state: FSMContext):
    """Получаем выбранную дату"""
    print(f"📅📅📅 ПОЛУЧИЛИ ДАТУ: {callback.data}")
    _, year, month, day = callback.data.split("_")
    selected_date = datetime(int(year), int(month), int(day))
    
    if selected_date.date() < datetime.now().date():
        await callback.answer("❌ Эта дата уже прошла", show_alert=True)
        return
    
    await state.update_data(selected_date=selected_date)
    print(f"✅ ДАТА СОХРАНЕНА: {selected_date}")
    
    await callback.message.edit_text(
        f"📅 *Выбрана дата:* {selected_date.strftime('%d.%m.%Y')}\n\n"
        f"🕒 *Выбери час*",
        parse_mode="Markdown",
        reply_markup=create_hour_keyboard()
    )
    await callback.answer()

@router.callback_query(CreateEventStates.waiting_for_date, F.data.startswith("hour_"))
async def process_hour_selected(callback: CallbackQuery, state: FSMContext):
    """Получаем выбранный час"""
    print(f"🕒🕒🕒 ПОЛУЧИЛИ ЧАС: {callback.data}")
    hour = int(callback.data.split("_")[1])
    await state.update_data(selected_hour=hour)
    
    print(f"✅ ЧАС СОХРАНЕН: {hour}")
    
    await callback.message.edit_text(
        f"📅 *Дата:* {await get_selected_date_str(state)}\n"
        f"🕒 *Выбран час:* {hour:02d}:__\n\n"
        f"⏱️ *Выбери минуты*",
        parse_mode="Markdown",
        reply_markup=create_minute_keyboard(hour)
    )
    await callback.answer()

@router.callback_query(CreateEventStates.waiting_for_date, F.data.startswith("minute_"))
async def process_minute_selected(callback: CallbackQuery, state: FSMContext):
    """Получаем выбранные минуты"""
    print(f"⏱️⏱️⏱️ ПОЛУЧИЛИ МИНУТЫ: {callback.data}")
    
    try:
        parts = callback.data.split("_")
        print(f"Разобранные части: {parts}")
        
        hour = int(parts[1])
        minute = int(parts[2])
        
        print(f"🕒 ВЫБРАННОЕ ВРЕМЯ: {hour:02d}:{minute:02d}")
        
        data = await state.get_data()
        selected_date = data.get('selected_date')
        
        print(f"📅 Выбранная дата из state: {selected_date}")
        
        if not selected_date:
            print("❌ ОШИБКА: ДАТА НЕ ВЫБРАНА")
            await callback.answer("❌ Ошибка: дата не выбрана", show_alert=True)
            return
        
        event_date = datetime(
            selected_date.year,
            selected_date.month,
            selected_date.day,
            hour,
            minute
        )
        
        print(f"📅 ИТОГОВАЯ ДАТА: {event_date}")
        
        if event_date < datetime.now():
            print("❌ ОШИБКА: ДАТА В ПРОШЛОМ")
            await callback.answer("❌ Дата и время не могут быть в прошлом!", show_alert=True)
            return
        
        await state.update_data(event_date=event_date)
        await state.set_state(CreateEventStates.waiting_for_price)
        
        print(f"✅ ВРЕМЯ СОХРАНЕНО, ПЕРЕХОД К ЦЕНЕ")
        
        builder = InlineKeyboardBuilder()
        builder.button(text="◀️ Назад", callback_data="back_to_date")
        builder.button(text="❌ Отмена", callback_data="cancel_price")
        builder.adjust(2)
        
        await callback.message.edit_text(
            f"✅ *Выбрано:* {event_date.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"💰 Теперь введи стоимость участия:",
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        
    except Exception as e:
        print(f"❌❌❌ КРИТИЧЕСКАЯ ОШИБКА В process_minute_selected: {e}")
        import traceback
        traceback.print_exc()
        await callback.answer("❌ Ошибка при выборе времени", show_alert=True)

@router.callback_query(CreateEventStates.waiting_for_date, F.data == "back_to_calendar")
async def back_to_calendar(callback: CallbackQuery, state: FSMContext):
    """Вернуться к календарю"""
    now = datetime.now()
    await callback.message.edit_text(
        "📅 *Выбери дату мероприятия*",
        parse_mode="Markdown",
        reply_markup=create_calendar(now.year, now.month)
    )
    await callback.answer()

@router.callback_query(CreateEventStates.waiting_for_date, F.data == "back_to_hour")
async def back_to_hour(callback: CallbackQuery, state: FSMContext):
    """Вернуться к выбору часа"""
    await callback.message.edit_text(
        f"📅 *Дата:* {await get_selected_date_str(state)}\n\n"
        f"🕒 *Выбери час*",
        parse_mode="Markdown",
        reply_markup=create_hour_keyboard()
    )
    await callback.answer()

@router.callback_query(CreateEventStates.waiting_for_date, F.data.startswith("cal_prev_"))
async def calendar_prev(callback: CallbackQuery, state: FSMContext):
    """Предыдущий месяц"""
    _, _, year, month = callback.data.split("_")
    year = int(year)
    month = int(month)
    
    if month == 1:
        month = 12
        year -= 1
    else:
        month -= 1
    
    await callback.message.edit_text(
        "📅 *Выбери дату мероприятия*",
        parse_mode="Markdown",
        reply_markup=create_calendar(year, month)
    )
    await callback.answer()

@router.callback_query(CreateEventStates.waiting_for_date, F.data.startswith("cal_next_"))
async def calendar_next(callback: CallbackQuery, state: FSMContext):
    """Следующий месяц"""
    _, _, year, month = callback.data.split("_")
    year = int(year)
    month = int(month)
    
    if month == 12:
        month = 1
        year += 1
    else:
        month += 1
    
    await callback.message.edit_text(
        "📅 *Выбери дату мероприятия*",
        parse_mode="Markdown",
        reply_markup=create_calendar(year, month)
    )
    await callback.answer()

@router.callback_query(CreateEventStates.waiting_for_date, F.data == "cancel_date")
async def cancel_date(callback: CallbackQuery, state: FSMContext):
    """Отмена выбора даты"""
    await state.clear()
    
    if callback.message.text:
        await callback.message.edit_text("❌ Создание мероприятия отменено")
    else:
        await callback.message.delete()
        await callback.message.answer("❌ Создание мероприятия отменено")
    
    await show_main_menu(callback.message)
    await callback.answer()

@router.callback_query(CreateEventStates.waiting_for_price, F.data == "back_to_date")
async def back_to_date_from_price(callback: CallbackQuery, state: FSMContext):
    """Вернуться к выбору даты"""
    await state.set_state(CreateEventStates.waiting_for_date)
    now = datetime.now()
    await callback.message.edit_text(
        "📅 *Выбери дату мероприятия*",
        parse_mode="Markdown",
        reply_markup=create_calendar(now.year, now.month)
    )
    await callback.answer()

@router.callback_query(CreateEventStates.waiting_for_price, F.data == "cancel_price")
async def cancel_price(callback: CallbackQuery, state: FSMContext):
    """Отмена создания"""
    await state.clear()
    
    if callback.message.text:
        await callback.message.edit_text("❌ Создание мероприятия отменено")
    else:
        await callback.message.delete()
        await callback.message.answer("❌ Создание мероприятия отменено")
    
    await show_main_menu(callback.message)
    await callback.answer()

@router.message(CreateEventStates.waiting_for_price)
async def process_price(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание отменено", reply_markup=None)
        await show_main_menu(message)
        return
    elif message.text == "◀️ Назад":
        await state.set_state(CreateEventStates.waiting_for_date)
        await ask_date(message, state)
        return
    
    price = message.text.strip()
    if len(price) > 50:
        await message.answer("Слишком длинное описание цены:")
        return
    
    await state.update_data(price=price)
    await state.set_state(CreateEventStates.waiting_for_participants)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="back_to_price")
    builder.button(text="❌ Отмена", callback_data="cancel_participants")
    builder.adjust(2)
    
    await message.answer(
        "👥 Сколько человек может участвовать?\n"
        "Напиши число (0 - без лимита)",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )

@router.callback_query(CreateEventStates.waiting_for_participants, F.data == "back_to_price")
async def back_to_price(callback: CallbackQuery, state: FSMContext):
    """Вернуться к вводу цены"""
    await state.set_state(CreateEventStates.waiting_for_price)
    await callback.message.edit_text(
        "💰 Введи стоимость участия:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardBuilder().button(
            text="❌ Отмена", callback_data="cancel_price"
        ).as_markup()
    )
    await callback.answer()

@router.callback_query(CreateEventStates.waiting_for_participants, F.data == "cancel_participants")
async def cancel_participants(callback: CallbackQuery, state: FSMContext):
    """Отмена создания"""
    await state.clear()
    
    if callback.message.text:
        await callback.message.edit_text("❌ Создание мероприятия отменено")
    else:
        await callback.message.delete()
        await callback.message.answer("❌ Создание мероприятия отменено")
    
    await show_main_menu(callback.message)
    await callback.answer()

@router.message(CreateEventStates.waiting_for_participants)
async def process_participants(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание отменено", reply_markup=None)
        await show_main_menu(message)
        return
    elif message.text == "◀️ Назад":
        await state.set_state(CreateEventStates.waiting_for_price)
        await message.answer(
            "💰 Введи стоимость:",
            reply_markup=InlineKeyboardBuilder().button(
                text="❌ Отмена", callback_data="cancel_price"
            ).as_markup()
        )
        return
    
    try:
        max_participants = int(message.text.strip())
        if max_participants < 0:
            await message.answer("Число должно быть положительным:")
            return
        
        await state.update_data(max_participants=max_participants)
        await state.set_state(CreateEventStates.waiting_for_chat_link)
        
        builder = InlineKeyboardBuilder()
        builder.button(text="◀️ Назад", callback_data="back_to_participants")
        builder.button(text="⏩ Пропустить", callback_data="skip_chat_link")
        builder.button(text="❌ Отмена", callback_data="cancel_chat_link")
        builder.adjust(2)
        
        await message.answer(
            "💬 *Чат мероприятия*\n\n"
            "Пришли ссылку на чат (или нажми «Пропустить»)",
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
    except ValueError:
        await message.answer("Введи число:")

@router.callback_query(CreateEventStates.waiting_for_chat_link, F.data == "back_to_participants")
async def back_to_participants(callback: CallbackQuery, state: FSMContext):
    """Вернуться к выбору количества участников"""
    await state.set_state(CreateEventStates.waiting_for_participants)
    await callback.message.edit_text(
        "👥 Введи количество участников:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardBuilder().button(
            text="❌ Отмена", callback_data="cancel_participants"
        ).as_markup()
    )
    await callback.answer()

@router.callback_query(CreateEventStates.waiting_for_chat_link, F.data == "skip_chat_link")
async def skip_chat_link(callback: CallbackQuery, state: FSMContext):
    """Пропустить добавление ссылки на чат"""
    await state.update_data(chat_link=None, chat_id=None)
    await show_preview(callback.message, state)
    await callback.answer()

@router.callback_query(CreateEventStates.waiting_for_chat_link, F.data == "cancel_chat_link")
async def cancel_chat_link(callback: CallbackQuery, state: FSMContext):
    """Отмена создания"""
    await state.clear()
    
    if callback.message.text:
        await callback.message.edit_text("❌ Создание мероприятия отменено")
    else:
        await callback.message.delete()
        await callback.message.answer("❌ Создание мероприятия отменено")
    
    await show_main_menu(callback.message)
    await callback.answer()

@router.message(CreateEventStates.waiting_for_chat_link)
async def process_chat_link(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание отменено", reply_markup=None)
        await show_main_menu(message)
        return
    elif message.text == "◀️ Назад":
        await state.set_state(CreateEventStates.waiting_for_participants)
        await message.answer(
            "👥 Введи количество участников:",
            reply_markup=InlineKeyboardBuilder().button(
                text="❌ Отмена", callback_data="cancel_participants"
            ).as_markup()
        )
        return
    elif message.text == "⏩ Пропустить":
        await state.update_data(chat_link=None, chat_id=None)
    else:
        link = message.text.strip()
        if "t.me/" in link:
            await state.update_data(chat_link=link, chat_id=None)
        else:
            await message.answer("❌ Это не похоже на ссылку Telegram. Нажми «Пропустить» или введи корректную ссылку:")
            return
    
    await show_preview(message, state)

async def show_preview(message: Message, state: FSMContext):
    data = await state.get_data()
    event_date_str = data['event_date'].strftime('%d.%m.%Y %H:%M')
    
    preview_text = (
        f"🌸 *Проверь данные встречи:*\n\n"
        f"*Название:* {data['title']}\n"
        f"*Категория:* {data['category']}\n"
        f"*Описание:* {data['description'] or 'Не указано'}\n"
        f"*Место:* {data['address']}\n"
        f"*Дата:* {event_date_str}\n"
        f"*Цена:* {data['price']}\n"
        f"*Участников:* {'Безлимит' if data['max_participants'] == 0 else data['max_participants']}\n"
    )
    
    if data.get('chat_link'):
        preview_text += f"*Чат:* [Ссылка]({data['chat_link']})\n"
    
    preview_text += f"\nВсё верно?"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, опубликовать", callback_data="confirm_event")
    builder.button(text="✏️ Редактировать", callback_data="edit_event")
    builder.button(text="❌ Отмена", callback_data="cancel_create")
    builder.adjust(1)
    
    await message.answer("...", reply_markup=None)
    
    if data.get('photo_file_id'):
        await message.answer_photo(
            photo=data['photo_file_id'],
            caption=preview_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
    else:
        await message.answer(preview_text, parse_mode="Markdown", reply_markup=builder.as_markup())

@router.callback_query(F.data == "confirm_event")
async def confirm_event(callback: CallbackQuery, state: FSMContext):
    print("✅ НАЖАТА КНОПКА 'ОПУБЛИКОВАТЬ'")
    
    data = await state.get_data()
    if not data:
        if callback.message.text:
            await callback.message.edit_text("❌ Ошибка: данные не найдены")
        else:
            await callback.message.delete()
            await callback.message.answer("❌ Ошибка: данные не найдены")
        await state.clear()
        await callback.answer()
        return
    
    user_id = callback.from_user.id
    data['district'] = "Минск"
    
    try:
        event_id = await add_event(
            creator_id=user_id,
            title=data['title'],
            description=data['description'],
            category=data['category'],
            photo_file_id=data.get('photo_file_id'),
            address=data['address'],
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            district=data['district'],
            event_date=data['event_date'],
            price=data['price'],
            max_participants=data['max_participants'],
            chat_link=data.get('chat_link'),
            chat_id=data.get('chat_id')
        )
        print(f"✅ Мероприятие сохранено с ID: {event_id}")
        
        await state.clear()
        
        if callback.message.text:
            await callback.message.edit_text(
                f"✅ *Мероприятие создано!*\n\n"
                f"Оно отправлено на модерацию. Проверка занимает до 2 часов.",
                parse_mode="Markdown"
            )
        else:
            await callback.message.delete()
            await callback.message.answer(
                f"✅ *Мероприятие создано!*\n\n"
                f"Оно отправлено на модерацию. Проверка занимает до 2 часов.",
                parse_mode="Markdown"
            )
        
        await show_main_menu(callback.message)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        if callback.message.text:
            await callback.message.edit_text(f"❌ Ошибка: {e}")
        else:
            await callback.message.delete()
            await callback.message.answer(f"❌ Ошибка: {e}")
    
    await callback.answer()

@router.callback_query(F.data == "edit_event")
async def edit_event(callback: CallbackQuery, state: FSMContext):
    if callback.message.text:
        await callback.message.edit_text("✏️ Редактирование в разработке")
    else:
        await callback.message.delete()
        await callback.message.answer("✏️ Редактирование в разработке")
    await state.clear()
    await show_main_menu(callback.message)
    await callback.answer()

@router.callback_query(F.data == "cancel_create")
async def cancel_create(callback: CallbackQuery, state: FSMContext):
    """Отмена создания"""
    await state.clear()
    
    if callback.message.text:
        await callback.message.edit_text("❌ Создание мероприятия отменено")
    else:
        await callback.message.delete()
        await callback.message.answer("❌ Создание мероприятия отменено")
    
    await show_main_menu(callback.message)
    await callback.answer()