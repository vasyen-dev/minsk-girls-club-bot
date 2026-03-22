from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from database.requests import get_user, update_user, delete_user, get_user_interests, get_all_interests, add_user_interests
from handlers.registration import check_age, show_main_menu
from handlers.interests import get_interests_keyboard, format_interests_text

router = Router()

# Список районов Минска
MINSK_DISTRICTS = [
    "Минск", "Центральный", "Советский", "Первомайский",
    "Партизанский", "Заводской", "Ленинский",
    "Октябрьский", "Московский", "Фрунзенский"
]

class EditProfileStates(StatesGroup):
    editing_name = State()
    editing_age = State()
    editing_district = State()
    editing_bio = State()
    editing_photo = State()
    editing_instagram = State()
    editing_interests = State()
    confirming_delete = State()

@router.message(F.text == "👤 Моя анкета")
async def show_profile(message: Message):
    print("👤 ПОКАЗ АНКЕТЫ - получена команда")
    user_id = message.from_user.id
    user = await get_user(user_id)
    
    if not user:
        await message.answer("❌ Ты не зарегистрирована. Напиши /start")
        return
    
    interests = await get_user_interests(user_id)
    interests_text = ", ".join([i.name for i in interests]) if interests else "Не выбраны"
    
    profile_text = (
        f"🌸 *Твоя анкета*\n\n"
        f"👤 *Имя:* {user.name}\n"
        f"🎂 *Возраст:* {user.age}\n"
        f"📍 *Район:* {user.district}\n"
        f"📝 *О себе:* {user.bio or 'Не указано'}\n"
        f"📸 *Instagram:* {user.instagram or 'Не указан'}\n"
        f"🎯 *Интересы:* {interests_text}\n\n"
        f"💗 С нами с {user.registered_at.strftime('%d.%m.%Y')}"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Редактировать", callback_data="edit_profile")
    builder.button(text="📸 Сменить фото", callback_data="edit_photo")
    builder.button(text="🎯 Интересы", callback_data="edit_interests")
    builder.button(text="❌ Выйти из клуба", callback_data="delete_profile")
    builder.button(text="🏠 В главное меню", callback_data="back_to_main_menu")
    builder.adjust(1)
    
    if user.photo_file_id:
        await message.answer_photo(
            photo=user.photo_file_id,
            caption=profile_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
    else:
        await message.answer(
            profile_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )

@router.callback_query(F.data == "back_to_main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    """Вернуться в главное меню"""
    print("🏠 ВОЗВРАТ В ГЛАВНОЕ МЕНЮ")
    await callback.message.delete()
    await show_main_menu(callback.message)
    await callback.answer()

@router.callback_query(F.data == "edit_profile")
async def edit_profile_menu(callback: CallbackQuery):
    print("✏️ НАЖАЛИ РЕДАКТИРОВАТЬ - callback получен")
    builder = InlineKeyboardBuilder()
    builder.button(text="👤 Имя", callback_data="edit_name")
    builder.button(text="🎂 Возраст", callback_data="edit_age")
    builder.button(text="📍 Район", callback_data="edit_district")
    builder.button(text="📝 О себе", callback_data="edit_bio")
    builder.button(text="📸 Instagram", callback_data="edit_instagram")
    builder.button(text="◀️ Назад", callback_data="back_to_profile")
    builder.adjust(2)
    
    if callback.message.text:
        await callback.message.edit_text(
            "✏️ *Что хочешь изменить?*",
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.delete()
        await callback.message.answer(
            "✏️ *Что хочешь изменить?*",
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
    
    await callback.answer()

@router.callback_query(F.data == "edit_name")
async def edit_name_start(callback: CallbackQuery, state: FSMContext):
    print("👤 НАЖАЛИ ИМЯ - callback получен")
    await state.set_state(EditProfileStates.editing_name)
    
    if callback.message.text:
        await callback.message.edit_text(
            "🌸 Введи новое имя:",
            reply_markup=InlineKeyboardBuilder().button(
                text="◀️ Отмена", callback_data="cancel_edit"
            ).as_markup()
        )
    else:
        await callback.message.delete()
        await callback.message.answer(
            "🌸 Введи новое имя:",
            reply_markup=InlineKeyboardBuilder().button(
                text="◀️ Отмена", callback_data="cancel_edit"
            ).as_markup()
        )
    
    await callback.answer()

@router.message(EditProfileStates.editing_name)
async def edit_name_process(message: Message, state: FSMContext):
    print("📝 ПОЛУЧИЛИ НОВОЕ ИМЯ")
    new_name = message.text.strip()
    
    if len(new_name) < 2 or len(new_name) > 50:
        await message.answer("Имя должно быть от 2 до 50 символов. Попробуй ещё раз:")
        return
    
    user_id = message.from_user.id
    await update_user(user_id, name=new_name)
    
    await state.clear()
    await message.answer("✅ Имя обновлено!")
    await show_profile(message)

@router.callback_query(F.data == "edit_age")
async def edit_age_start(callback: CallbackQuery, state: FSMContext):
    print("🎂 НАЖАЛИ ВОЗРАСТ - callback получен")
    await state.set_state(EditProfileStates.editing_age)
    
    if callback.message.text:
        await callback.message.edit_text(
            "🎂 Введи свой возраст (18-29):",
            reply_markup=InlineKeyboardBuilder().button(
                text="◀️ Отмена", callback_data="cancel_edit"
            ).as_markup()
        )
    else:
        await callback.message.delete()
        await callback.message.answer(
            "🎂 Введи свой возраст (18-29):",
            reply_markup=InlineKeyboardBuilder().button(
                text="◀️ Отмена", callback_data="cancel_edit"
            ).as_markup()
        )
    
    await callback.answer()

@router.message(EditProfileStates.editing_age)
async def edit_age_process(message: Message, state: FSMContext):
    print("📝 ПОЛУЧИЛИ НОВЫЙ ВОЗРАСТ")
    try:
        new_age = int(message.text.strip())
        
        if not check_age(new_age):
            await message.answer("❌ Возраст должен быть от 18 до 29 лет. Попробуй ещё раз:")
            return
        
        user_id = message.from_user.id
        await update_user(user_id, age=new_age)
        
        await state.clear()
        await message.answer("✅ Возраст обновлён!")
        await show_profile(message)
        
    except ValueError:
        await message.answer("Пожалуйста, введи возраст числом:")

@router.callback_query(F.data == "edit_district")
async def edit_district_start(callback: CallbackQuery, state: FSMContext):
    print("📍 НАЖАЛИ РАЙОН - callback получен")
    await state.set_state(EditProfileStates.editing_district)
    
    builder = ReplyKeyboardBuilder()
    for district in MINSK_DISTRICTS:
        builder.button(text=district)
    builder.adjust(2)
    
    await callback.message.delete()
    await callback.message.answer(
        "📍 Выбери свой район:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )
    await callback.answer()

@router.message(EditProfileStates.editing_district)
async def edit_district_process(message: Message, state: FSMContext):
    print("📝 ПОЛУЧИЛИ НОВЫЙ РАЙОН")
    new_district = message.text.strip()
    
    if new_district not in MINSK_DISTRICTS:
        await message.answer("Пожалуйста, выбери район из списка 👇")
        return
    
    user_id = message.from_user.id
    await update_user(user_id, district=new_district)
    
    await state.clear()
    await message.answer("✅ Район обновлён!", reply_markup=None)
    await show_profile(message)

@router.callback_query(F.data == "edit_bio")
async def edit_bio_start(callback: CallbackQuery, state: FSMContext):
    print("📝 НАЖАЛИ О СЕБЕ - callback получен")
    await state.set_state(EditProfileStates.editing_bio)
    
    if callback.message.text:
        await callback.message.edit_text(
            "📝 Напиши немного о себе:\n"
            "(или отправь «пропустить», чтобы удалить описание)",
            reply_markup=InlineKeyboardBuilder().button(
                text="◀️ Отмена", callback_data="cancel_edit"
            ).as_markup()
        )
    else:
        await callback.message.delete()
        await callback.message.answer(
            "📝 Напиши немного о себе:\n"
            "(или отправь «пропустить», чтобы удалить описание)",
            reply_markup=InlineKeyboardBuilder().button(
                text="◀️ Отмена", callback_data="cancel_edit"
            ).as_markup()
        )
    
    await callback.answer()

@router.message(EditProfileStates.editing_bio)
async def edit_bio_process(message: Message, state: FSMContext):
    print("📝 ПОЛУЧИЛИ НОВОЕ О СЕБЕ")
    new_bio = message.text.strip()
    
    if new_bio.lower() == "пропустить":
        new_bio = None
        await message.answer("Описание удалено")
    
    user_id = message.from_user.id
    await update_user(user_id, bio=new_bio)
    
    await state.clear()
    await message.answer("✅ Описание обновлено!")
    await show_profile(message)

@router.callback_query(F.data == "edit_instagram")
async def edit_instagram_start(callback: CallbackQuery, state: FSMContext):
    print("📸 НАЖАЛИ INSTAGRAM - callback получен")
    await state.set_state(EditProfileStates.editing_instagram)
    
    if callback.message.text:
        await callback.message.edit_text(
            "📸 Введи свой Instagram-ник:\n"
            "(или «пропустить», чтобы удалить)",
            reply_markup=InlineKeyboardBuilder().button(
                text="◀️ Отмена", callback_data="cancel_edit"
            ).as_markup()
        )
    else:
        await callback.message.delete()
        await callback.message.answer(
            "📸 Введи свой Instagram-ник:\n"
            "(или «пропустить», чтобы удалить)",
            reply_markup=InlineKeyboardBuilder().button(
                text="◀️ Отмена", callback_data="cancel_edit"
            ).as_markup()
        )
    
    await callback.answer()

@router.message(EditProfileStates.editing_instagram)
async def edit_instagram_process(message: Message, state: FSMContext):
    print("📝 ПОЛУЧИЛИ НОВЫЙ INSTAGRAM")
    new_instagram = message.text.strip()
    
    if new_instagram.lower() == "пропустить":
        new_instagram = None
        await message.answer("Instagram удалён")
    
    user_id = message.from_user.id
    await update_user(user_id, instagram=new_instagram)
    
    await state.clear()
    await message.answer("✅ Instagram обновлён!")
    await show_profile(message)

@router.callback_query(F.data == "edit_photo")
async def edit_photo_start(callback: CallbackQuery, state: FSMContext):
    print("📸 НАЖАЛИ СМЕНИТЬ ФОТО - callback получен")
    await state.set_state(EditProfileStates.editing_photo)
    
    if callback.message.text:
        await callback.message.edit_text(
            "📸 Отправь новое фото:\n"
            "(или «удалить», чтобы убрать текущее)",
            reply_markup=InlineKeyboardBuilder().button(
                text="◀️ Отмена", callback_data="cancel_edit"
            ).as_markup()
        )
    else:
        await callback.message.delete()
        await callback.message.answer(
            "📸 Отправь новое фото:\n"
            "(или «удалить», чтобы убрать текущее)",
            reply_markup=InlineKeyboardBuilder().button(
                text="◀️ Отмена", callback_data="cancel_edit"
            ).as_markup()
        )
    
    await callback.answer()

@router.message(EditProfileStates.editing_photo, F.photo)
async def edit_photo_process(message: Message, state: FSMContext):
    print("📸 ПОЛУЧИЛИ НОВОЕ ФОТО")
    photo_file_id = message.photo[-1].file_id
    user_id = message.from_user.id
    await update_user(user_id, photo_file_id=photo_file_id)
    
    await state.clear()
    await message.answer("✅ Фото обновлено!")
    await show_profile(message)

@router.message(EditProfileStates.editing_photo)
async def edit_photo_delete(message: Message, state: FSMContext):
    print("📝 ПОПЫТКА УДАЛИТЬ ФОТО")
    if message.text and message.text.lower() == "удалить":
        user_id = message.from_user.id
        await update_user(user_id, photo_file_id=None)
        
        await state.clear()
        await message.answer("✅ Фото удалено")
        await show_profile(message)
    else:
        await message.answer("Отправь фото или напиши «удалить»")

@router.callback_query(F.data == "edit_interests")
async def edit_interests_start(callback: CallbackQuery, state: FSMContext):
    print("🎯 НАЖАЛИ ИНТЕРЕСЫ - callback получен")
    await state.set_state(EditProfileStates.editing_interests)
    
    all_interests = await get_all_interests()
    user_id = callback.from_user.id
    user_interests = await get_user_interests(user_id)
    user_interest_ids = [i.id for i in user_interests]
    
    await state.update_data(selected_interests=user_interest_ids)
    
    keyboard = await get_interests_keyboard(all_interests, user_interest_ids, "edit_interest")
    selected_text = format_interests_text(user_interest_ids, all_interests)
    
    if callback.message.text:
        await callback.message.edit_text(
            f"🎯 *Редактирование интересов*\n\n"
            f"{selected_text}\n\n"
            f"👉 Нажимай на интересы, чтобы изменить выбор\n"
            f"✅ Минимум 3 интереса",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    else:
        await callback.message.delete()
        await callback.message.answer(
            f"🎯 *Редактирование интересов*\n\n"
            f"{selected_text}\n\n"
            f"👉 Нажимай на интересы, чтобы изменить выбор\n"
            f"✅ Минимум 3 интереса",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    
    await callback.answer()

@router.callback_query(EditProfileStates.editing_interests, F.data.startswith("edit_interest_"))
async def toggle_interest_edit(callback: CallbackQuery, state: FSMContext):
    """Выбор/отмена интереса при редактировании"""
    try:
        interest_id = int(callback.data.split("_")[2])
        print(f"🔍 Редактирование: выбран интерес {interest_id}")
        
        data = await state.get_data()
        selected = data.get('selected_interests', [])
        
        if interest_id in selected:
            selected.remove(interest_id)
            print(f"❌ Интерес {interest_id} удален")
        else:
            selected.append(interest_id)
            print(f"✅ Интерес {interest_id} добавлен")
        
        await state.update_data(selected_interests=selected)
        
        # Обновляем клавиатуру
        all_interests = await get_all_interests()
        keyboard = await get_interests_keyboard(all_interests, selected, "edit_interest")
        selected_text = format_interests_text(selected, all_interests)
        
        await callback.message.edit_text(
            f"🎯 *Редактирование интересов*\n\n"
            f"{selected_text}\n\n"
            f"👉 Нажимай на интересы, чтобы изменить выбор\n"
            f"✅ Минимум 3 интереса",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        await callback.answer()
    except Exception as e:
        print(f"❌ Ошибка в toggle_interest_edit: {e}")
        await callback.answer("❌ Ошибка при выборе", show_alert=True)

@router.callback_query(EditProfileStates.editing_interests, F.data == "interests_save")
async def interests_save_edit(callback: CallbackQuery, state: FSMContext):
    """Сохранить изменения интересов"""
    data = await state.get_data()
    selected = data.get('selected_interests', [])
    
    if len(selected) < 3:
        await callback.answer("❌ Минимум 3 интереса!", show_alert=True)
        return
    
    user_id = callback.from_user.id
    await add_user_interests(user_id, selected)
    
    await state.clear()
    await callback.message.edit_text("✅ Интересы обновлены!")
    await show_profile(callback.message)

@router.callback_query(EditProfileStates.editing_interests, F.data == "interests_back")
async def interests_back_edit(callback: CallbackQuery, state: FSMContext):
    """Назад к анкете без сохранения"""
    await state.clear()
    await back_to_profile(callback)

@router.callback_query(F.data == "delete_profile")
async def delete_profile_start(callback: CallbackQuery, state: FSMContext):
    print("❌ НАЖАЛИ ВЫЙТИ ИЗ КЛУБА - callback получен")
    await state.set_state(EditProfileStates.confirming_delete)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Да, хочу удалить", callback_data="confirm_delete")
    builder.button(text="🌸 Нет, остаюсь", callback_data="back_to_profile")
    builder.adjust(1)
    
    if callback.message.text:
        await callback.message.edit_text(
            "💔 *Точно хочешь уйти?*\n\n"
            "Все твои данные и записи на мероприятия будут удалены.\n"
            "Это действие нельзя отменить.",
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.delete()
        await callback.message.answer(
            "💔 *Точно хочешь уйти?*\n\n"
            "Все твои данные и записи на мероприятия будут удалены.\n"
            "Это действие нельзя отменить.",
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
    
    await callback.answer()

@router.callback_query(F.data == "confirm_delete")
async def delete_profile_confirm(callback: CallbackQuery, state: FSMContext):
    print("✅ ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ")
    user_id = callback.from_user.id
    await delete_user(user_id)
    
    await state.clear()
    await callback.message.edit_text(
        "💔 Твой профиль удалён.\n\n"
        "Если захочешь вернуться — напиши /start в любой момент 🌸"
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_profile")
async def back_to_profile(callback: CallbackQuery, state: FSMContext = None):
    print("◀️ НАЗАД К АНКЕТЕ")
    if state:
        await state.clear()
    
    user_id = callback.from_user.id
    user = await get_user(user_id)
    
    if not user:
        await callback.message.answer("❌ Ошибка загрузки профиля")
        return
    
    interests = await get_user_interests(user_id)
    interests_text = ", ".join([i.name for i in interests]) if interests else "Не выбраны"
    
    profile_text = (
        f"🌸 *Твоя анкета*\n\n"
        f"👤 *Имя:* {user.name}\n"
        f"🎂 *Возраст:* {user.age}\n"
        f"📍 *Район:* {user.district}\n"
        f"📝 *О себе:* {user.bio or 'Не указано'}\n"
        f"📸 *Instagram:* {user.instagram or 'Не указан'}\n"
        f"🎯 *Интересы:* {interests_text}\n\n"
        f"💗 С нами с {user.registered_at.strftime('%d.%m.%Y')}"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Редактировать", callback_data="edit_profile")
    builder.button(text="📸 Сменить фото", callback_data="edit_photo")
    builder.button(text="🎯 Интересы", callback_data="edit_interests")
    builder.button(text="❌ Выйти из клуба", callback_data="delete_profile")
    builder.button(text="🏠 В главное меню", callback_data="back_to_main_menu")
    builder.adjust(1)
    
    await callback.message.delete()
    
    if user.photo_file_id:
        await callback.message.answer_photo(
            photo=user.photo_file_id,
            caption=profile_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.answer(
            profile_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
    
    await callback.answer()

@router.callback_query(F.data == "cancel_edit")
async def cancel_edit(callback: CallbackQuery, state: FSMContext):
    print("❌ ОТМЕНА РЕДАКТИРОВАНИЯ")
    await state.clear()
    await back_to_profile(callback)

@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: CallbackQuery):
    await callback.answer()