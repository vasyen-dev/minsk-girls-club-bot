from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from database.requests import add_user, user_exists

router = Router()

class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_bio = State()
    waiting_for_photo = State()
    waiting_for_instagram = State()

def check_age(age: int) -> bool:
    return 18 <= age <= 29

def get_cancel_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Отмена")
    return builder.as_markup(resize_keyboard=True)

def get_nav_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="◀️ Назад")
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

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    if await user_exists(user_id):
        await show_main_menu(message)
        return
    
    await state.set_state(RegistrationStates.waiting_for_name)
    await message.answer(
        "🌸 Привет! Это *Minsk Girls Club* — клуб для своих\n\n"
        "Давай познакомимся! Как тебя зовут?\n"
        "(Можно имя или ник, как тебе комфортно)",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )

@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()
    
    if name == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Регистрация отменена", reply_markup=None)
        return
    
    if len(name) < 2 or len(name) > 50:
        await message.answer("Имя должно быть от 2 до 50 символов. Попробуй ещё раз:")
        return
    
    await state.update_data(name=name)
    await state.set_state(RegistrationStates.waiting_for_age)
    
    await message.answer(
        f"Приятно познакомиться, {name} 💗\n\n"
        "Сколько тебе лет?",
        reply_markup=get_nav_keyboard()
    )

@router.message(RegistrationStates.waiting_for_age)
async def process_age(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Регистрация отменена", reply_markup=None)
        return
    elif message.text == "◀️ Назад":
        await state.set_state(RegistrationStates.waiting_for_name)
        await message.answer(
            "🌸 Введи своё имя:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    try:
        age = int(message.text.strip())
        
        if not check_age(age):
            await message.answer(
                "❌ Наш клуб для девушек 18-29 лет.\n"
                "Если ты подходишь по возрасту, напиши корректное число:"
            )
            return
        
        await state.update_data(age=age)
        await state.set_state(RegistrationStates.waiting_for_bio)
        
        await message.answer(
            "Класс! А теперь расскажи немного о себе 😊\n"
            "Например: чем увлекаешься, что ищешь в клубе, может у тебя есть хобби?",
            reply_markup=get_nav_keyboard()
        )
        
    except ValueError:
        await message.answer("Пожалуйста, введи возраст числом:")

@router.message(RegistrationStates.waiting_for_bio)
async def process_bio(message: Message, state: FSMContext):
    text = message.text.strip()
    
    if text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Регистрация отменена", reply_markup=None)
        return
    elif text == "◀️ Назад":
        await state.set_state(RegistrationStates.waiting_for_age)
        await message.answer(
            "🎂 Введи свой возраст:",
            reply_markup=get_nav_keyboard()
        )
        return
    
    await state.update_data(bio=text)
    await state.set_state(RegistrationStates.waiting_for_photo)
    
    await message.answer(
        "Загрузи своё фото 📸\n"
        "Так девочкам будет приятнее общаться и легче узнать тебя на встречах",
        reply_markup=get_skip_keyboard()
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
    text = message.text.strip() if message.text else ""
    
    if text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Регистрация отменена", reply_markup=None)
        return
    elif text == "◀️ Назад":
        await state.set_state(RegistrationStates.waiting_for_bio)
        await message.answer(
            "📝 Напиши немного о себе:",
            reply_markup=get_nav_keyboard()
        )
        return
    elif text == "⏩ Пропустить":
        await state.update_data(photo_file_id=None)
        await state.set_state(RegistrationStates.waiting_for_instagram)
        await ask_instagram(message)
    else:
        await message.answer("Отправь фото или нажми кнопку «Пропустить» 📸")

async def ask_instagram(message: Message):
    await message.answer(
        "Оставь свой Instagram, если хочешь ✨\n"
        "Организаторы мероприятий смогут легко связаться с тобой",
        reply_markup=get_skip_keyboard()
    )

@router.message(RegistrationStates.waiting_for_instagram)
async def process_instagram(message: Message, state: FSMContext):
    text = message.text.strip()
    
    if text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Регистрация отменена", reply_markup=None)
        return
    elif text == "◀️ Назад":
        await state.set_state(RegistrationStates.waiting_for_photo)
        await message.answer(
            "📸 Загрузи своё фото:",
            reply_markup=get_skip_keyboard()
        )
        return
    elif text == "⏩ Пропустить":
        instagram = None
        await message.answer("Окей, можно будет добавить позже ✨", reply_markup=None)
    else:
        # Убираем @ если есть
        instagram = text.replace("@", "")
        await message.answer("Спасибо! 💗", reply_markup=None)
    
    await state.update_data(instagram=instagram)
    
    # Сохраняем пользователя
    user_data = await state.get_data()
    user_id = message.from_user.id
    username = message.from_user.username
    
    await add_user(
        user_id=user_id,
        username=username,
        name=user_data['name'],
        age=user_data['age'],
        district="Минск",
        bio=user_data.get('bio'),
        photo_file_id=user_data.get('photo_file_id'),
        instagram=user_data.get('instagram')
    )
    
    await state.clear()
    
    await message.answer(
        "💗 *Поздравляем! Ты стала частью Minsk Girls Club!*\n\n"
        "Теперь ты можешь:\n"
        "🌸 Находить мероприятия по душе\n"
        "✨ Создавать свои встречи\n"
        "👭 Знакомиться с классными девчонками\n\n"
        "Погнали! 🚀",
        parse_mode="Markdown"
    )
    
    await show_main_menu(message)

async def show_main_menu(message: Message):
    """Показывает главное меню"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="🌸 Найти событие")
    builder.button(text="✨ Создать встречу")
    builder.button(text="📅 Мои планы")
    builder.button(text="💬 Чат клуба")
    builder.button(text="👤 Моя анкета")
    builder.adjust(2)
    
    await message.answer(
        "🌸 *Главное меню*\n\n"
        "Куда отправимся?",
        parse_mode="Markdown",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )