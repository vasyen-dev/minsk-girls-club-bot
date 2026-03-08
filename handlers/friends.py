from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.requests import get_user, get_all_users, add_friend, remove_friend, get_friends, get_fans, get_user_interests
from database.requests import is_friend, is_fan

router = Router()

# Храним текущие списки пользователей для навигации
user_lists = {}

@router.message(F.text == "👭 Подруги")
async def cmd_friends(message: Message):
    """Главное меню раздела подруги"""
    print(f"\n🔍 ===== НАЖАТА КНОПКА ПОДРУГИ =====")
    print(f"🔍 ID пользователя: {message.from_user.id}")
    print(f"🔍 Текст сообщения: {message.text}")
    
    user_id = message.from_user.id
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔍 Найти подруг", callback_data="find_friends")
    builder.button(text="💗 Мои подруги", callback_data="my_friends")
    builder.button(text="📋 Кто меня добавил", callback_data="my_fans")
    builder.adjust(1)
    
    sent_message = await message.answer(
        "👭 *Раздел подруг*\n\n"
        "Здесь ты можешь найти новых знакомых и общаться!",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )
    print(f"✅ Сообщение отправлено, ID: {sent_message.message_id}")

@router.callback_query(F.data == "find_friends")
async def find_friends(callback: CallbackQuery):
    """Найти новых подруг"""
    print(f"\n🔍 ===== НАЖАТА КНОПКА НАЙТИ ПОДРУГ =====")
    print(f"🔍 ID пользователя: {callback.from_user.id}")
    print(f"🔍 Callback data: {callback.data}")
    
    user_id = callback.from_user.id
    
    # Получаем всех пользователей, кроме себя
    print(f"🔍 Получаем всех пользователей...")
    all_users = await get_all_users()
    print(f"🔍 Всего пользователей в БД: {len(all_users)}")
    
    other_users = [u for u in all_users if u.user_id != user_id]
    print(f"🔍 Других пользователей (кроме себя): {len(other_users)}")
    
    if not other_users:
        print(f"❌ Нет других пользователей")
        await callback.message.edit_text(
            "😔 Пока нет других участниц\n\n"
            "Пригласи подруг в клуб!",
            reply_markup=InlineKeyboardBuilder().button(
                text="◀️ Назад", callback_data="back_to_friends"
            ).as_markup()
        )
        await callback.answer()
        return
    
    # Сохраняем список для навигации
    user_lists[user_id] = {
        'list': [u.user_id for u in other_users],
        'current_index': 0,
        'mode': 'find'
    }
    print(f"✅ Сохранен список пользователей: {user_lists[user_id]}")
    
    await callback.message.delete()
    await show_friend_profile(callback.message, user_id, 0, "find")
    await callback.answer()

@router.callback_query(F.data == "my_friends")
async def my_friends(callback: CallbackQuery):
    """Показать список подруг"""
    print(f"\n🔍 ===== НАЖАТА КНОПКА МОИ ПОДРУГИ =====")
    print(f"🔍 ID пользователя: {callback.from_user.id}")
    print(f"🔍 Callback data: {callback.data}")
    
    user_id = callback.from_user.id
    
    # Получаем список подруг
    print(f"🔍 Получаем список подруг...")
    friends = await get_friends(user_id)
    print(f"🔍 Найдено подруг: {len(friends)}")
    
    if not friends:
        print(f"❌ Нет подруг")
        await callback.message.edit_text(
            "💗 У тебя пока нет подруг\n\n"
            "Нажми «🔍 Найти подруг», чтобы добавить!",
            reply_markup=InlineKeyboardBuilder().button(
                text="◀️ Назад", callback_data="back_to_friends"
            ).as_markup()
        )
        await callback.answer()
        return
    
    # Сохраняем список для навигации
    user_lists[user_id] = {
        'list': [f.friend_id for f in friends],
        'current_index': 0,
        'mode': 'friends'
    }
    print(f"✅ Сохранен список подруг: {user_lists[user_id]}")
    
    await callback.message.delete()
    await show_friend_profile(callback.message, user_id, 0, "friends")
    await callback.answer()

@router.callback_query(F.data == "my_fans")
async def my_fans(callback: CallbackQuery):
    """Показать, кто добавил пользователя"""
    print(f"\n🔍 ===== НАЖАТА КНОПКА КТО МЕНЯ ДОБАВИЛ =====")
    print(f"🔍 ID пользователя: {callback.from_user.id}")
    print(f"🔍 Callback data: {callback.data}")
    
    user_id = callback.from_user.id
    
    # Получаем список тех, кто добавил пользователя
    print(f"🔍 Получаем список фанатов...")
    fans = await get_fans(user_id)
    print(f"🔍 Найдено фанатов: {len(fans)}")
    
    if not fans:
        print(f"❌ Нет фанатов")
        await callback.message.edit_text(
            "😔 Пока никто не добавил тебя в подруги",
            reply_markup=InlineKeyboardBuilder().button(
                text="◀️ Назад", callback_data="back_to_friends"
            ).as_markup()
        )
        await callback.answer()
        return
    
    # Сохраняем список для навигации
    user_lists[user_id] = {
        'list': [f.user_id for f in fans],
        'current_index': 0,
        'mode': 'fans'
    }
    print(f"✅ Сохранен список фанатов: {user_lists[user_id]}")
    
    await callback.message.delete()
    await show_friend_profile(callback.message, user_id, 0, "fans")
    await callback.answer()

async def show_friend_profile(message: Message, user_id: int, index: int, mode: str):
    """Показать профиль подруги"""
    print(f"\n🔍 ===== ПОКАЗ ПРОФИЛЯ ПОДРУГИ =====")
    print(f"🔍 Для пользователя: {user_id}")
    print(f"🔍 Индекс: {index}, режим: {mode}")
    
    lists = user_lists.get(user_id, {})
    print(f"🔍 Данные из user_lists: {lists}")
    
    friend_ids = lists.get('list', [])
    print(f"🔍 Список ID друзей: {friend_ids}")
    
    if not friend_ids:
        print(f"❌ Список friend_ids пуст")
        await message.answer("😔 Список пуст")
        return
    
    if index >= len(friend_ids):
        print(f"❌ Индекс {index} больше длины списка {len(friend_ids)}")
        await message.answer("😔 Список пуст")
        return
    
    friend_id = friend_ids[index]
    print(f"🔍 Загружаем профиль подруги с ID: {friend_id}")
    
    friend = await get_user(friend_id)
    
    if not friend:
        print(f"❌ Профиль с ID {friend_id} не найден")
        await message.answer("❌ Ошибка загрузки профиля")
        return
    
    print(f"✅ Профиль загружен: {friend.name}, возраст: {friend.age}")
    
    # Получаем интересы подруги отдельным запросом
    print(f"🔍 Загружаем интересы...")
    interests = await get_user_interests(friend_id)
    interests_text = ", ".join([i.name for i in interests]) if interests else "Не выбраны"
    print(f"✅ Интересы: {interests_text}")
    
    # Проверяем, является ли подругой
    print(f"🔍 Проверяем, является ли подругой...")
    is_friend_flag = await is_friend(user_id, friend_id)
    print(f"✅ Является подругой: {is_friend_flag}")
    
    # Проверяем, добавила ли она в ответ
    print(f"🔍 Проверяем, добавила ли она в ответ...")
    is_fan_flag = await is_fan(user_id, friend_id)
    print(f"✅ Добавила в ответ: {is_fan_flag}")
    
    # Формируем текст профиля
    profile_text = (
        f"👭 *Профиль*\n\n"
        f"👤 *Имя:* {friend.name}\n"
        f"🎂 *Возраст:* {friend.age}\n"
        f"📍 *Район:* {friend.district}\n"
        f"📝 *О себе:* {friend.bio or 'Не указано'}\n"
        f"🎯 *Интересы:* {interests_text}\n"
    )
    
    # Если она уже добавила тебя, показываем это
    if is_fan_flag and not is_friend_flag:
        profile_text += "\n✨ Она уже добавила тебя в подруги!"
    
    print(f"🔍 Текст профиля сформирован")
    
    builder = InlineKeyboardBuilder()
    
    # Кнопки в зависимости от режима
    if mode == "find":
        if is_friend_flag:
            builder.button(text="❌ Удалить из подруг", callback_data=f"remove_friend_{friend_id}")
        else:
            builder.button(text="💗 Добавить в подруги", callback_data=f"add_friend_{friend_id}")
    
    elif mode == "friends":
        builder.button(text="❌ Удалить", callback_data=f"remove_friend_{friend_id}")
    
    elif mode == "fans":
        if not is_friend_flag:
            builder.button(text="💗 Добавить в ответ", callback_data=f"add_friend_{friend_id}")
    
    # Кнопка для связи
    if friend.username:
        builder.button(text="📱 Написать в Telegram", url=f"https://t.me/{friend.username}")
    elif friend.instagram:
        builder.button(text="📸 Написать в Instagram", url=f"https://instagram.com/{friend.instagram}")
    
    # Навигация
    nav_builder = InlineKeyboardBuilder()
    if index > 0:
        nav_builder.button(text="◀️", callback_data=f"prev_friend_{mode}")
    if index < len(friend_ids) - 1:
        nav_builder.button(text="▶️", callback_data=f"next_friend_{mode}")
    
    if nav_builder.buttons:
        builder.attach(nav_builder)
    
    builder.button(text="🏠 В меню", callback_data="back_to_friends")
    builder.adjust(2)
    
    print(f"🔍 Кнопки созданы, отправляем сообщение...")
    
    if friend.photo_file_id:
        sent = await message.answer_photo(
            photo=friend.photo_file_id,
            caption=profile_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
    else:
        sent = await message.answer(
            profile_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
    
    print(f"✅ Сообщение отправлено, ID: {sent.message_id}")

@router.callback_query(F.data.startswith("prev_friend_"))
async def prev_friend(callback: CallbackQuery):
    """Предыдущая подруга"""
    mode = callback.data.split("_")[2]
    user_id = callback.from_user.id
    
    print(f"\n🔍 ===== ПРЕДЫДУЩАЯ ПОДРУГА =====")
    print(f"🔍 Режим: {mode}, пользователь: {user_id}")
    
    lists = user_lists.get(user_id, {})
    current_index = lists.get('current_index', 0)
    print(f"🔍 Текущий индекс: {current_index}")
    
    if current_index > 0:
        lists['current_index'] = current_index - 1
        print(f"✅ Новый индекс: {current_index - 1}")
        await callback.message.delete()
        await show_friend_profile(callback.message, user_id, current_index - 1, mode)
    else:
        print(f"❌ Нельзя перейти назад, уже первый")
    
    await callback.answer()

@router.callback_query(F.data.startswith("next_friend_"))
async def next_friend(callback: CallbackQuery):
    """Следующая подруга"""
    mode = callback.data.split("_")[2]
    user_id = callback.from_user.id
    
    print(f"\n🔍 ===== СЛЕДУЮЩАЯ ПОДРУГА =====")
    print(f"🔍 Режим: {mode}, пользователь: {user_id}")
    
    lists = user_lists.get(user_id, {})
    current_index = lists.get('current_index', 0)
    friend_ids = lists.get('list', [])
    print(f"🔍 Текущий индекс: {current_index}, всего друзей: {len(friend_ids)}")
    
    if current_index < len(friend_ids) - 1:
        lists['current_index'] = current_index + 1
        print(f"✅ Новый индекс: {current_index + 1}")
        await callback.message.delete()
        await show_friend_profile(callback.message, user_id, current_index + 1, mode)
    else:
        print(f"❌ Нельзя перейти вперед, уже последний")
    
    await callback.answer()

@router.callback_query(F.data.startswith("add_friend_"))
async def add_friend_callback(callback: CallbackQuery):
    """Добавить в подруги"""
    friend_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    print(f"\n🔍 ===== ДОБАВЛЕНИЕ В ПОДРУГИ =====")
    print(f"🔍 Пользователь {user_id} добавляет {friend_id}")
    
    result = await add_friend(user_id, friend_id)
    
    if result:
        print(f"✅ Успешно добавлено")
        await callback.answer("💗 Добавлено в подруги!", show_alert=True)
    else:
        print(f"❌ Ошибка или уже в подругах")
        await callback.answer("❌ Уже в подругах", show_alert=True)
    
    # Обновляем текущий профиль
    lists = user_lists.get(user_id, {})
    mode = lists.get('mode', 'find')
    current_index = lists.get('current_index', 0)
    
    await callback.message.delete()
    await show_friend_profile(callback.message, user_id, current_index, mode)

@router.callback_query(F.data.startswith("remove_friend_"))
async def remove_friend_callback(callback: CallbackQuery):
    """Удалить из подруг"""
    friend_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    print(f"\n🔍 ===== УДАЛЕНИЕ ИЗ ПОДРУГ =====")
    print(f"🔍 Пользователь {user_id} удаляет {friend_id}")
    
    result = await remove_friend(user_id, friend_id)
    
    if result:
        print(f"✅ Успешно удалено")
        await callback.answer("❌ Удалено из подруг", show_alert=True)
    else:
        print(f"❌ Ошибка удаления")
        await callback.answer("❌ Ошибка", show_alert=True)
    
    # Обновляем текущий профиль
    lists = user_lists.get(user_id, {})
    mode = lists.get('mode', 'find')
    current_index = lists.get('current_index', 0)
    
    await callback.message.delete()
    await show_friend_profile(callback.message, user_id, current_index, mode)

@router.callback_query(F.data == "back_to_friends")
async def back_to_friends(callback: CallbackQuery):
    """Вернуться в главное меню подруг"""
    print(f"\n🔍 ===== НАЗАД В МЕНЮ ПОДРУГ =====")
    print(f"🔍 Пользователь: {callback.from_user.id}")
    
    await callback.message.delete()
    await cmd_friends(callback.message)
    await callback.answer()