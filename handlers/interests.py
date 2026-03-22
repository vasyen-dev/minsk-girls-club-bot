from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

async def get_interests_keyboard(all_interests, selected_ids, action_prefix="interest"):
    """
    Создает клавиатуру с интересами (простой список без категорий)
    
    all_interests: список всех интересов из БД
    selected_ids: список ID выбранных интересов
    action_prefix: префикс для callback_data (interest или edit_interest)
    """
    builder = InlineKeyboardBuilder()
    
    # Сортируем интересы по названию для удобства
    sorted_interests = sorted(all_interests, key=lambda x: x.name)
    
    # Создаем простой список кнопок
    for interest in sorted_interests:
        if interest.id in selected_ids:
            # Выбранный интерес с зеленой галочкой
            builder.button(text=f"✅ {interest.name}", callback_data=f"{action_prefix}_{interest.id}")
        else:
            # Невыбранный интерес с серым кружочком
            builder.button(text=f"⚪️ {interest.name}", callback_data=f"{action_prefix}_{interest.id}")
    
    # Кнопки управления
    builder.button(text="🔝 В начало", callback_data="interests_scroll_top")
    builder.button(text="✅ Сохранить", callback_data="interests_save")
    builder.button(text="◀️ Назад", callback_data="interests_back")
    builder.adjust(2)  # Кнопки управления в ряд по 2
    
    return builder.as_markup()

def format_interests_text(selected_ids, all_interests):
    """Форматирует текст с количеством выбранных интересов"""
    if not selected_ids:
        return "❌ Пока ничего не выбрано"
    
    selected_names = []
    for interest in all_interests:
        if interest.id in selected_ids:
            selected_names.append(interest.name)
    
    if len(selected_names) <= 3:
        return f"✨ Выбрано: {len(selected_ids)} шт.\n📌 {', '.join(selected_names)}"
    else:
        return f"✨ Выбрано: {len(selected_ids)} шт.\n📌 {', '.join(selected_names[:3])}..."

@router.callback_query(F.data == "interests_scroll_top")
async def interests_scroll_top(callback: CallbackQuery):
    """Прокрутка вверх (отправляет сообщение с инструкцией)"""
    await callback.answer("👆 Ты в начале списка", show_alert=False)