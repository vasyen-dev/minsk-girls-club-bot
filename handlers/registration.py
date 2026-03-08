from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from database.requests import add_user, user_exists, get_all_interests, add_user_interests
from handlers.interests import get_interests_keyboard, format_interests_text

router = Router()

class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_district = State()
    waiting_for_bio = State()
    waiting_for_photo = State()
    waiting_for_interests = State()
    waiting_for_instagram = State()

MINSK_DISTRICTS = [
    "Центральный", "Советский", "Первомайский",
    "Партизанский", "Заводской", "Ленинский",
    "Октябрьский", "Московский", "Фрунзенский"
]

def check_age(age: int) -> bool:
    return 18 <= age <= 29

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    if await user_exists(user_id):
        await show_main_menu(message)
        return
    
    await state.set_state(RegistrationStates.waiting_for_name)
    await message.answer(
        "🌸 Привет! Это *SVOI Minsk Girls* — клуб для своих\n\n"
        "Давай познакомимся! Как тебя зовут?\n"
        "(Можно имя или ник, как тебе комфортно)",
        parse_mode="Markdown"
    )

@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()
    
    if len(name) < 2 or len(name) > 50:
        await message.answer("Имя должно быть от 2 до 50 символов. Попробуй ещё раз:")
        return
    
    await state.update_data(name=name)
    await state.set_state(RegistrationStates.waiting_for_age)
    
    await message.answer(
        f"Приятно познакомиться, {name} 💗\n\n"
        "Сколько тебе лет?"
    )

@router.message(RegistrationStates.waiting_for_age)
async def process_age(message: Message, state: FSMContext):
    try:
        age = int(message.text.strip())
        
        if not check_age(age):
            await message.answer(
                "❌ Наш клуб для девушек 18-29 лет.\n"
                "Если ты подходишь по возрасту, напиши корректное число:"
            )
            return
        
        await state.update_data(age=age)
        await state.set_state(RegistrationStates.waiting_for_district)
        
        builder = ReplyKeyboardBuilder()
        for district in MINSK_DISTRICTS:
            builder.button(text=district)
        builder.adjust(2)
        
        await message.answer(
            "В каком районе Минска ты живёшь или чаще всего бываешь?\n"
            "Это поможет показывать мероприятия поближе к тебе 🌸",
            reply_markup=builder.as_markup(resize_keyboard=True)
        )
        
    except ValueError:
        await message.answer("Пожалуйста, введи возраст числом:")

@router.message(RegistrationStates.waiting_for_district)
async def process_district(message: Message, state: FSMContext):
    district = message.text.strip()
    
    if district not in MINSK_DISTRICTS:
        await message.answer("Пожалуйста, выбери район из списка 👇")
        return
    
    await state.update_data(district=district)
    await state.set_state(RegistrationStates.waiting_for_bio)
    
    await message.answer(
        "Класс! А теперь расскажи немного о себе 😊\n"
        "Например: чем увлекаешься, что ищешь в клубе, может у тебя есть хобби?\n\n"
        "(Можно пропустить, написав «пропустить»)",
        reply_markup=ReplyKeyboardBuilder().button(text="🚫 Пропустить").as_markup(resize_keyboard=True)
    )

@router.message(RegistrationStates.waiting_for_bio)
async def process_bio(message: Message, state: FSMContext):
    bio = message.text.strip()
    
    if bio.lower() == "пропустить":
        bio = None
        await message.answer("Окей, расскажешь потом 👌", reply_markup=None)
    else:
        await message.answer("Интересно! Запомнила 💫", reply_markup=None)
    
    await state.update_data(bio=bio)
    await state.set_state(RegistrationStates.waiting_for_photo)
    
    await message.answer(
        "Загрузи своё фото 📸\n"
        "Так девочкам будет приятнее общаться и легче узнать тебя на встречах\n\n"
        "(Можно пропустить)"
    )

@router.message(RegistrationStates.waiting_for_photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    photo_file_id = message.photo[-1].file_id
    await state.update_data(photo_file_id=photo_file_id)
    
    await message.answer("Красивое фото! 💗")
    await state.set_state(RegistrationStates.waiting_for_instagram)
    await ask_instagram(message)

@router.message(RegistrationStates.waiting_for_photo)
async def process_photo_skip(message: Message, state: FSMContext):
    if message.text and message.text.lower() == "пропустить":
        await state.update_data(photo_file_id=None)
        await state.set_state(RegistrationStates.waiting_for_instagram)
        await ask_instagram(message)
    else:
        await message.answer("Отправь фото или напиши «пропустить» 📸")

async def ask_instagram(message: Message):
    await message.answer(
        "Оставь свой Instagram, если хочешь ✨\n"
        "Организаторы мероприятий смогут легко связаться с тобой\n\n"
        "(Напиши ник или «пропустить»)"
    )

@router.message(RegistrationStates.waiting_for_instagram)
async def process_instagram(message: Message, state: FSMContext):
    instagram = message.text.strip()
    
    if instagram.lower() == "пропустить":
        instagram = None
    
    await state.update_data(instagram=instagram)
    await state.set_state(RegistrationStates.waiting_for_interests)
    await show_interests_selection(message, state)

async def show_interests_selection(message: Message, state: FSMContext):
    """Показывает интересы с возможностью выбора"""
    interests = await get_all_interests()
    data = await state.get_data()
    selected = data.get('selected_interests', [])
    
    keyboard = await get_interests_keyboard(interests, selected, "reg_interest")
    selected_text = format_interests_text(selected, interests)
    
    await message.answer(
        f"🌸 *Выбери свои интересы*\n\n"
        f"{selected_text}\n\n"
        f"👉 Нажимай на интересы, чтобы выбрать\n"
        f"✅ Минимум 3 интереса",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@router.callback_query(RegistrationStates.waiting_for_interests, F.data.startswith("reg_interest_"))
async def toggle_interest_reg(callback: CallbackQuery, state: FSMContext):
    """Выбор/отмена интереса при регистрации"""
    interest_id = int(callback.data.split("_")[2])
    data = await state.get_data()
    selected = data.get('selected_interests', [])
    
    if interest_id in selected:
        selected.remove(interest_id)
    else:
        selected.append(interest_id)
    
    await state.update_data(selected_interests=selected)
    
    # Обновляем клавиатуру
    interests = await get_all_interests()
    keyboard = await get_interests_keyboard(interests, selected, "reg_interest")
    selected_text = format_interests_text(selected, interests)
    
    await callback.message.edit_text(
        f"🌸 *Выбери свои интересы*\n\n"
        f"{selected_text}\n\n"
        f"👉 Нажимай на интересы, чтобы выбрать\n"
        f"✅ Минимум 3 интереса",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(RegistrationStates.waiting_for_interests, F.data == "interests_save")
async def interests_save_reg(callback: CallbackQuery, state: FSMContext):
    """Сохранить выбранные интересы при регистрации"""
    data = await state.get_data()
    selected = data.get('selected_interests', [])
    
    if len(selected) < 3:
        await callback.answer("❌ Нужно выбрать минимум 3 интереса!", show_alert=True)
        return
    
    # Получаем все данные пользователя
    user_data = await state.get_data()
    user_id = callback.from_user.id
    username = callback.from_user.username
    
    await add_user(
        user_id=user_id,
        username=username,
        name=user_data['name'],
        age=user_data['age'],
        district=user_data['district'],
        bio=user_data.get('bio'),
        photo_file_id=user_data.get('photo_file_id'),
        instagram=user_data.get('instagram')
    )
    
    await add_user_interests(user_id, selected)
    await state.clear()
    
    await callback.message.edit_text(
        "💗 *Поздравляем! Ты стала частью SVOI Minsk Girls!*\n\n"
        "Теперь ты можешь:\n"
        "🌸 Находить мероприятия по душе\n"
        "✨ Создавать свои встречи\n"
        "👭 Знакомиться с классными девчонками\n\n"
        "Погнали! 🚀",
        parse_mode="Markdown"
    )
    
    await show_main_menu(callback.message)

@router.callback_query(RegistrationStates.waiting_for_interests, F.data == "interests_back")
async def interests_back_reg(callback: CallbackQuery, state: FSMContext):
    """Назад при регистрации"""
    await state.set_state(RegistrationStates.waiting_for_instagram)
    await callback.message.delete()
    await ask_instagram(callback.message)
    await callback.answer()

async def show_main_menu(message: Message):
    """Показывает главное меню"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="🌸 Найти событие")
    builder.button(text="✨ Создать встречу")
    builder.button(text="📅 Мои планы")
    builder.button(text="👭 Подруги")
    builder.button(text="💬 Чат клуба")
    builder.button(text="👤 Моя анкета")
    builder.adjust(2)
    
    await message.answer(
        "🌸 *Главное меню*\n\n"
        "Куда отправимся?",
        parse_mode="Markdown",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )