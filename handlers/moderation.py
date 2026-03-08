from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime

from database.requests import get_pending_events, approve_event, reject_event, get_user
from database.models import Interest
from config import ADMIN_IDS
from database.requests import Session

router = Router()

async def get_category_name(category_id):
    """Получить название категории по ID"""
    if not category_id:
        return "Не указана"
    
    with Session() as session:
        category = session.get(Interest, category_id)
        return category.name if category else "Не указана"

@router.message(Command("moderate"))
async def cmd_moderate(message: Message):
    """Начать модерацию (команда для админов)"""
    print("\n🔍 ===== ПОЛУЧЕНА КОМАНДА /moderate =====")
    print(f"🔍 ID пользователя: {message.from_user.id}")
    print(f"🔍 ADMIN_IDS из config: {ADMIN_IDS}")
    print(f"🔍 Является админом? {message.from_user.id in ADMIN_IDS}")
    
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У тебя нет прав администратора")
        return
    
    await show_next_event(message)

async def show_next_event(message: Message):
    """Показать следующее мероприятие на модерацию"""
    print("\n🔍 ===== ПОКАЗ МЕРОПРИЯТИЙ НА МОДЕРАЦИЮ =====")
    
    events = await get_pending_events()
    print(f"🔍 Получено мероприятий: {len(events)}")
    
    if not events:
        await message.answer("✅ Новых мероприятий на модерации нет")
        return
    
    event = events[0]
    print(f"🔍 Показываем мероприятие ID: {event.event_id}, название: {event.title}")
    
    # Получаем данные создателя
    creator = await get_user(event.creator_id)
    creator_name = creator.name if creator else "Неизвестно"
    
    # Получаем название категории
    category_name = await get_category_name(event.category_id)
    
    # Форматируем дату
    event_date = event.event_date.strftime('%d.%m.%Y %H:%M')
    
    text = (
        f"📝 *Новое мероприятие*\n\n"
        f"*Название:* {event.title}\n"
        f"*Категория:* {category_name}\n"
        f"*Описание:* {event.description or 'Нет описания'}\n"
        f"*Место:* {event.address}\n"
        f"*Дата:* {event_date}\n"
        f"*Цена:* {event.price}\n"
        f"*Участников:* {'Безлимит' if event.max_participants == 0 else event.max_participants}\n"
        f"*Создатель:* {creator_name}\n\n"
        f"*Действие:*"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Опубликовать", callback_data=f"approve_{event.event_id}")
    builder.button(text="❌ Отклонить", callback_data=f"reject_{event.event_id}")
    builder.button(text="➡️ Пропустить", callback_data="next_event")
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

@router.callback_query(F.data.startswith("approve_"))
async def approve_event_callback(callback: CallbackQuery):
    """Одобрить мероприятие"""
    event_id = int(callback.data.split("_")[1])
    print(f"\n🔍 ===== НАЖАТА КНОПКА ОДОБРИТЬ =====")
    print(f"✅ Одобряем мероприятие ID: {event_id}")
    print(f"🔍 От пользователя: {callback.from_user.id}")
    
    try:
        result = await approve_event(event_id)
        if result:
            print(f"✅ Мероприятие {event_id} успешно одобрено")
            await callback.message.delete()
            await show_next_event(callback.message)
            await callback.answer("✅ Мероприятие опубликовано!")
        else:
            print(f"❌ Ошибка: мероприятие {event_id} не найдено")
            await callback.answer("❌ Ошибка: мероприятие не найдено", show_alert=True)
    except Exception as e:
        print(f"❌ Ошибка при одобрении: {e}")
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)

@router.callback_query(F.data.startswith("reject_"))
async def reject_event_callback(callback: CallbackQuery):
    """Отклонить мероприятие"""
    event_id = int(callback.data.split("_")[1])
    print(f"\n🔍 ===== НАЖАТА КНОПКА ОТКЛОНИТЬ =====")
    print(f"❌ Отклоняем мероприятие ID: {event_id}")
    print(f"🔍 От пользователя: {callback.from_user.id}")
    
    try:
        result = await reject_event(event_id)
        if result:
            print(f"✅ Мероприятие {event_id} успешно отклонено")
            await callback.message.delete()
            await show_next_event(callback.message)
            await callback.answer("❌ Мероприятие отклонено!")
        else:
            print(f"❌ Ошибка: мероприятие {event_id} не найдено")
            await callback.answer("❌ Ошибка: мероприятие не найдено", show_alert=True)
    except Exception as e:
        print(f"❌ Ошибка при отклонении: {e}")
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)

@router.callback_query(F.data == "next_event")
async def next_event_callback(callback: CallbackQuery):
    """Пропустить текущее и показать следующее"""
    print(f"\n🔍 ===== НАЖАТА КНОПКА ПРОПУСТИТЬ =====")
    print(f"➡️ Пропускаем мероприятие")
    print(f"🔍 От пользователя: {callback.from_user.id}")
    
    await callback.message.delete()
    await show_next_event(callback.message)
    await callback.answer("➡️ Следующее мероприятие")