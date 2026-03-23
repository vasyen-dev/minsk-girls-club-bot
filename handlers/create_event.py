from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from datetime import datetime

from database.requests import get_user, get_all_interests, add_event
from handlers.registration import show_main_menu
from handlers.categories import EVENT_CATEGORIES

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

# Клавиатура с кнопками назад и отмена
def get_navigation_keyboard(show_back=True, show_cancel=True):
    builder = ReplyKeyboardBuilder()
    if show_back:
        builder.button(text="◀️ Назад")
    if show_cancel:
        builder.button(text="❌ Отмена")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# Клавиатура для шагов с пропуском (назад + пропустить + отмена)
def get_skip_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="◀️ Назад")
    builder.button(text="⏩ Пропустить")
    builder.button(text="❌ Отмена")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

@router.message(F.text == "✨ Создать встречу")
async def cmd_create_event(message: Message, state: FSMContext):
    """Начало создания мероприятия"""
    print("🌸 НАЧАЛО СОЗДАНИЯ МЕРОПРИЯТИЯ")
    user_id = message.from_user.id
    user = await get_user(user_id)
    
    if not user:
        await message.answer("❌ Сначала нужно зарегистрироваться! Напиши /start")
        return
    
    await state.set_state(CreateEventStates.waiting_for_title)
    await message.answer(
        "🌸 *Создание новой встречи*\n\n"
        "Давай придумаем название! Как назовём мероприятие?\n"
        "(Например: «Йога в парке», «Девичник в бане», «Мастер-класс по макияжу»)",
        parse_mode="Markdown",
        reply_markup=get_navigation_keyboard(show_back=False, show_cancel=True)
    )

@router.message(CreateEventStates.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    """Получаем название"""
    print("📝 ПОЛУЧИЛИ НАЗВАНИЕ")
    
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание отменено", reply_markup=None)
        await show_main_menu(message)
        return
    
    title = message.text.strip()
    
    if len(title) < 3 or len(title) > 100:
        await message.answer("Название должно быть от 3 до 100 символов. Попробуй ещё раз:")
        return
    
    await state.update_data(title=title)
    await state.set_state(CreateEventStates.waiting_for_description)
    
    await message.answer(
        f"Отлично! Название: *{title}*\n\n"
        "Теперь напиши описание мероприятия 📝\n"
        "Расскажи, чем будем заниматься, что брать с собой, какие особенности",
        parse_mode="Markdown",
        reply_markup=get_navigation_keyboard(show_back=True, show_cancel=True)
    )

@router.message(CreateEventStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    """Получаем описание (обязательно)"""
    print("📝 ПОЛУЧИЛИ ОПИСАНИЕ")
    
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание отменено", reply_markup=None)
        await show_main_menu(message)
        return
    elif message.text == "◀️ Назад":
        await state.set_state(CreateEventStates.waiting_for_title)
        await message.answer(
            "🌸 Введи название заново:",
            reply_markup=get_navigation_keyboard(show_back=False, show_cancel=True)
        )
        return
    
    description = message.text.strip()
    
    if len(description) < 10:
        await message.answer("Описание должно быть не менее 10 символов. Расскажи подробнее о встрече:")
        return
    
    if len(description) > 1000:
        await message.answer("Описание слишком длинное (максимум 1000 символов). Сократи, пожалуйста:")
        return
    
    await state.update_data(description=description)
    await state.set_state(CreateEventStates.waiting_for_category)
    
    # Показываем категории для выбора
    await show_categories(message, state)

async def show_categories(message: Message, state: FSMContext):
    """Показывает 6 категорий для выбора"""
    print("📋 ПОКАЗЫВАЕМ КАТЕГОРИИ")
    
    builder = InlineKeyboardBuilder()
    for category in EVENT_CATEGORIES:
        builder.button(text=category, callback_data=f"cat_{category}")
    
    builder.button(text="◀️ Назад", callback_data="back_to_description")
    builder.button(text="❌ Отмена", callback_data="cancel_create")
    builder.adjust(2)
    
    await message.answer(
        "Выбери категорию мероприятия:",
        reply_markup=builder.as_markup()
    )

@router.callback_query(CreateEventStates.waiting_for_category, F.data.startswith("cat_"))
async def process_category(callback: CallbackQuery, state: FSMContext):
    """Получаем категорию"""
    print("📋 ПОЛУЧИЛИ КАТЕГОРИЮ")
    category = callback.data[4:]  # убираем "cat_"
    print(f"Категория: {category}")
    
    await state.update_data(category=category)
    await state.set_state(CreateEventStates.waiting_for_photo)
    
    await callback.message.edit_text(
        f"Категория: *{category}*\n\n"
        "Теперь загрузи фото для мероприятия 📸\n"
        "Это поможет привлечь больше участниц\n\n"
        "(Можно пропустить, нажав кнопку ниже)"
    )
    
    await callback.message.answer(
        "👇 Выбери действие:",
        reply_markup=get_skip_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_description")
async def back_to_description(callback: CallbackQuery, state: FSMContext):
    """Вернуться к описанию"""
    await state.set_state(CreateEventStates.waiting_for_description)
    await callback.message.delete()
    await callback.message.answer(
        "📝 Напиши описание заново:",
        reply_markup=get_navigation_keyboard(show_back=True, show_cancel=True)
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_create")
async def cancel_create_callback(callback: CallbackQuery, state: FSMContext):
    """Отмена создания"""
    await state.clear()
    await callback.message.edit_text("❌ Создание мероприятия отменено")
    await show_main_menu(callback.message)
    await callback.answer()

@router.message(CreateEventStates.waiting_for_photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    """Получаем фото"""
    print("📸 ПОЛУЧИЛИ ФОТО")
    
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
    """Пропускаем фото или отменяем (кнопками)"""
    print("📸 ОБРАБОТКА ФОТО")
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
        await message.answer("Отправь фото или нажми кнопку «Пропустить» 📸")

async def ask_location(message: Message, state: FSMContext):
    """Спрашиваем место проведения"""
    print("📍 СПРАШИВАЕМ МЕСТО")
    await message.answer(
        "📍 Где пройдёт встреча?\n\n"
        "Ты можешь отправить геолокацию или написать адрес текстом",
        reply_markup=get_navigation_keyboard(show_back=True, show_cancel=True)
    )

@router.message(CreateEventStates.waiting_for_location, F.location)
async def process_location(message: Message, state: FSMContext):
    """Получаем геолокацию"""
    print("📍 ПОЛУЧИЛИ ГЕОЛОКАЦИЮ")
    
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание отменено", reply_markup=None)
        await show_main_menu(message)
        return
    elif message.text == "◀️ Назад":
        await state.set_state(CreateEventStates.waiting_for_photo)
        await message.answer(
            "📸 Загрузи фото заново:",
            reply_markup=get_skip_keyboard()
        )
        return
    
    latitude = message.location.latitude
    longitude = message.location.longitude
    
    await state.update_data(
        latitude=str(latitude),
        longitude=str(longitude),
        address="📍 По геолокации"
    )
    
    await state.set_state(CreateEventStates.waiting_for_date)
    await ask_date(message, state)

@router.message(CreateEventStates.waiting_for_location)
async def process_address(message: Message, state: FSMContext):
    """Получаем адрес текстом"""
    print("📍 ПОЛУЧИЛИ АДРЕС")
    
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание отменено", reply_markup=None)
        await show_main_menu(message)
        return
    elif message.text == "◀️ Назад":
        await state.set_state(CreateEventStates.waiting_for_photo)
        await message.answer(
            "📸 Загрузи фото заново:",
            reply_markup=get_skip_keyboard()
        )
        return
    
    address = message.text.strip()
    
    await state.update_data(
        address=address,
        latitude=None,
        longitude=None
    )
    
    await state.set_state(CreateEventStates.waiting_for_date)
    await ask_date(message, state)

async def ask_date(message: Message, state: FSMContext):
    """Спрашиваем дату и время"""
    print("🕒 СПРАШИВАЕМ ДАТУ")
    await message.answer(
        "🕒 Когда состоится встреча?\n\n"
        "Напиши дату и время в формате:\n"
        "`ДД.ММ.ГГГГ ЧЧ:ММ`\n\n"
        "Например: `25.12.2024 19:00`",
        parse_mode="Markdown",
        reply_markup=get_navigation_keyboard(show_back=True, show_cancel=True)
    )

@router.message(CreateEventStates.waiting_for_date)
async def process_date(message: Message, state: FSMContext):
    """Получаем дату и время"""
    print("🕒 ПОЛУЧИЛИ ДАТУ")
    
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание отменено", reply_markup=None)
        await show_main_menu(message)
        return
    elif message.text == "◀️ Назад":
        await state.set_state(CreateEventStates.waiting_for_location)
        await ask_location(message, state)
        return
    
    date_text = message.text.strip()
    
    try:
        clean_date = date_text.replace("г.", "").replace(" ", " ").strip()
        event_date = datetime.strptime(clean_date, "%d.%m.%Y %H:%M")
        
        if event_date < datetime.now():
            await message.answer("❌ Дата не может быть в прошлом! Введи будущую дату:")
            return
        
        await state.update_data(event_date=event_date)
        await state.set_state(CreateEventStates.waiting_for_price)
        
        await message.answer(
            "💰 Стоимость участия?\n\n"
            "Варианты:\n"
            "• `Бесплатно`\n"
            "• `Донат` (кто сколько хочет)\n"
            "• `10 руб.` (или другая сумма)\n\n"
            "Напиши свой вариант:",
            parse_mode="Markdown",
            reply_markup=get_navigation_keyboard(show_back=True, show_cancel=True)
        )
        
    except ValueError:
        await message.answer("❌ Неправильный формат! Используй: `ДД.ММ.ГГГГ ЧЧ:ММ`\nНапример: 25.12.2024 19:00", parse_mode="Markdown")

@router.message(CreateEventStates.waiting_for_price)
async def process_price(message: Message, state: FSMContext):
    """Получаем стоимость"""
    print("💰 ПОЛУЧИЛИ ЦЕНУ")
    
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
        await message.answer("Слишком длинное описание цены. Покороче, пожалуйста:")
        return
    
    await state.update_data(price=price)
    await state.set_state(CreateEventStates.waiting_for_participants)
    
    await message.answer(
        "👥 Сколько человек может участвовать?\n\n"
        "Напиши число (например: `10`)\n"
        "Или `0`, если нет ограничений",
        parse_mode="Markdown",
        reply_markup=get_navigation_keyboard(show_back=True, show_cancel=True)
    )

@router.message(CreateEventStates.waiting_for_participants)
async def process_participants(message: Message, state: FSMContext):
    """Получаем количество участников"""
    print("👥 ПОЛУЧИЛИ КОЛИЧЕСТВО УЧАСТНИКОВ")
    
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание отменено", reply_markup=None)
        await show_main_menu(message)
        return
    elif message.text == "◀️ Назад":
        await state.set_state(CreateEventStates.waiting_for_price)
        await message.answer(
            "💰 Введи стоимость заново:",
            reply_markup=get_navigation_keyboard(show_back=True, show_cancel=True)
        )
        return
    
    try:
        max_participants = int(message.text.strip())
        
        if max_participants < 0:
            await message.answer("Число должно быть положительным. Попробуй ещё раз:")
            return
        
        await state.update_data(max_participants=max_participants)
        
        await state.set_state(CreateEventStates.waiting_for_chat_link)
        await message.answer(
            "💬 *Чат мероприятия*\n\n"
            "Если хочешь создать чат для участниц, сделай это сейчас:\n\n"
            "1️⃣ Создай чат в Telegram\n"
            "2️⃣ Пришли сюда ссылку на чат (или нажми «Пропустить»)\n\n"
            "Это поможет участницам общаться до встречи!",
            parse_mode="Markdown",
            reply_markup=get_skip_keyboard()
        )
        
    except ValueError:
        await message.answer("Введи число (например: 10) или 0 для безлимита:")

@router.message(CreateEventStates.waiting_for_chat_link)
async def process_chat_link(message: Message, state: FSMContext):
    """Получаем ссылку на чат (с кнопкой пропустить)"""
    print("💬 ПОЛУЧИЛИ ССЫЛКУ НА ЧАТ")
    
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание отменено", reply_markup=None)
        await show_main_menu(message)
        return
    elif message.text == "◀️ Назад":
        await state.set_state(CreateEventStates.waiting_for_participants)
        await message.answer(
            "👥 Введи количество участников заново:",
            reply_markup=get_navigation_keyboard(show_back=True, show_cancel=True)
        )
        return
    elif message.text == "⏩ Пропустить":
        await state.update_data(chat_link=None, chat_id=None)
    else:
        link = message.text.strip()
        if "t.me/" in link or "telegram.me/" in link or "https://t.me/" in link:
            await state.update_data(chat_link=link, chat_id=None)
        else:
            await message.answer("❌ Это не похоже на ссылку Telegram. Попробуй ещё раз или нажми «Пропустить»:")
            return
    
    await show_preview(message, state)

async def show_preview(message: Message, state: FSMContext):
    """Показывает превью мероприятия перед сохранением"""
    print("👀 ПОКАЗЫВАЕМ ПРЕВЬЮ")
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
        preview_text += f"*Чат:* [Ссылка на чат]({data['chat_link']})\n"
    
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
        await message.answer(
            preview_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )

@router.callback_query(F.data == "confirm_event")
async def confirm_event(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и сохранение мероприятия"""
    print("✅ НАЖАТА КНОПКА 'ОПУБЛИКОВАТЬ'")
    
    data = await state.get_data()
    
    if not data:
        if callback.message.text:
            await callback.message.edit_text("❌ Ошибка: данные не найдены. Начни создание заново.")
        else:
            await callback.message.delete()
            await callback.message.answer("❌ Ошибка: данные не найдены. Начни создание заново.")
        await state.clear()
        await callback.answer()
        return
    
    user_id = callback.from_user.id
    data['district'] = "Минск"  # Район по умолчанию
    
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
                f"Оно отправлено на модерацию. Обычно проверка занимает до 2 часов.\n"
                f"Мы уведомим тебя, когда встреча будет опубликована 🌸",
                parse_mode="Markdown"
            )
        else:
            await callback.message.delete()
            await callback.message.answer(
                f"✅ *Мероприятие создано!*\n\n"
                f"Оно отправлено на модерацию. Обычно проверка занимает до 2 часов.\n"
                f"Мы уведомим тебя, когда встреча будет опубликована 🌸",
                parse_mode="Markdown"
            )
        
        await show_main_menu(callback.message)
        
    except Exception as e:
        print(f"❌ Ошибка при сохранении: {e}")
        if callback.message.text:
            await callback.message.edit_text(f"❌ Ошибка при сохранении: {e}")
        else:
            await callback.message.delete()
            await callback.message.answer(f"❌ Ошибка при сохранении: {e}")
    
    await callback.answer()

@router.callback_query(F.data == "edit_event")
async def edit_event(callback: CallbackQuery, state: FSMContext):
    """Редактирование мероприятия"""
    print("✏️ НАЖАТА КНОПКА 'РЕДАКТИРОВАТЬ'")
    
    if callback.message.text:
        await callback.message.edit_text(
            "✏️ Редактирование\n\n"
            "Пока эта функция в разработке. Начни создание заново с /start"
        )
    else:
        await callback.message.delete()
        await callback.message.answer(
            "✏️ Редактирование\n\n"
            "Пока эта функция в разработке. Начни создание заново с /start"
        )
    
    await state.clear()
    await show_main_menu(callback.message)
    await callback.answer()

@router.callback_query(F.data == "cancel_create")
async def cancel_create(callback: CallbackQuery, state: FSMContext):
    """Отмена создания"""
    print("❌ НАЖАТА КНОПКА 'ОТМЕНА'")
    
    if callback.message.text:
        await callback.message.edit_text("❌ Создание мероприятия отменено")
    else:
        await callback.message.delete()
        await callback.message.answer("❌ Создание мероприятия отменено")
    
    await state.clear()
    await show_main_menu(callback.message)
    await callback.answer()