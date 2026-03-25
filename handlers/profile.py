from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from database.requests import get_user, update_user, delete_user
from handlers.registration import check_age, show_main_menu

router = Router()

class EditProfileStates(StatesGroup):
    editing_name = State()
    editing_age = State()
    editing_bio = State()
    editing_photo = State()
    editing_instagram = State()
    confirming_delete = State()

@router.message(F.text == "👤 Моя анкета")
async def show_profile(message: Message):
    print("👤 ПОКАЗ АНКЕТЫ - получена команда")
    user_id = message.from_user.id
    user = await get_user(user_id)
    
    if not user:
        await message.answer("❌ Ты не зарегистрирована. Напиши /start")
        return
    
    profile_text = (
        f"🌸 *Твоя анкета*\n\n"
        f"👤 *Имя:* {user.name}\n"
        f"🎂 *Возраст:* {user.age}\n"
        f"📝 *О себе:* {user.bio or 'Не указано'}\n"
    )
    
    if user.instagram:
        insta_clean = user.instagram.replace("@", "")
        profile_text += f"📸 *Instagram:* [{user.instagram}](https://instagram.com/{insta_clean})\n"
    else:
        profile_text += f"📸 *Instagram:* Не указан\n"
    
    profile_text += f"\n💗 С нами с {user.registered_at.strftime('%d.%m.%Y')}"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Редактировать", callback_data="edit_profile")
    builder.button(text="📸 Сменить фото", callback_data="edit_photo")
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
    else:
        new_instagram = new_instagram.replace("@", "")
        await message.answer("✅ Instagram обновлён!")
    
    user_id = message.from_user.id
    await update_user(user_id, instagram=new_instagram)
    
    await state.clear()
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
    
    if callback.message.text:
        await callback.message.edit_text(
            "💔 Твой профиль удалён.\n\n"
            "Если захочешь вернуться — напиши /start в любой момент 🌸"
        )
    else:
        await callback.message.delete()
        await callback.message.answer(
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
    
    profile_text = (
        f"🌸 *Твоя анкета*\n\n"
        f"👤 *Имя:* {user.name}\n"
        f"🎂 *Возраст:* {user.age}\n"
        f"📝 *О себе:* {user.bio or 'Не указано'}\n"
    )
    
    if user.instagram:
        insta_clean = user.instagram.replace("@", "")
        profile_text += f"📸 *Instagram:* [{user.instagram}](https://instagram.com/{insta_clean})\n"
    else:
        profile_text += f"📸 *Instagram:* Не указан\n"
    
    profile_text += f"\n💗 С нами с {user.registered_at.strftime('%d.%m.%Y')}"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Редактировать", callback_data="edit_profile")
    builder.button(text="📸 Сменить фото", callback_data="edit_photo")
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