from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

# Словарь смайликов для категорий
CATEGORY_EMOJIS = {
    "Красота и здоровье": "💄",
    "Творчество": "🎨",
    "Общение": "💬",
    "Активности": "🏃‍♀️",
    "Развлечения": "🎬"
}

async def get_interests_keyboard(all_interests, selected_ids, action_prefix="interest"):
    """
    Создает клавиатуру с интересами, где выбранные отмечены галочкой
    
    all_interests: список всех интересов из БД
    selected_ids: список ID выбранных интересов
    action_prefix: префикс для callback_data (interest или edit_interest)
    """
    builder = InlineKeyboardBuilder()
    
    # Группируем по категориям
    categories = {}
    for interest in all_interests:
        if interest.category not in categories:
            categories[interest.category] = []
        categories[interest.category].append(interest)
    
    # Создаем кнопки по категориям
    for category, cat_interests in categories.items():
        # Получаем смайлик для категории (или ставим точку, если нет в словаре)
        emoji = CATEGORY_EMOJIS.get(category, "•")
        
        # Заголовок категории с тематическим смайликом (некликабельный)
        builder.button(text=f"{emoji} {category}", callback_data="ignore_category")
        
        # Интересы в категории
        for interest in cat_interests:
            if interest.id in selected_ids:
                # Выбранный интерес с зеленой галочкой
                builder.button(text=f"✅ {interest.name}", callback_data=f"{action_prefix}_{interest.id}")
            else:
                # Невыбранный интерес с серым кружочком
                builder.button(text=f"⚪️ {interest.name}", callback_data=f"{action_prefix}_{interest.id}")
        
        builder.adjust(1)  # Каждая категория с новой строки
    
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
    """Прокрутка вверх"""
    print("🔍 НАЖАТА КНОПКА: interests_scroll_top")
    await callback.answer("👆 Ты в начале списка", show_alert=False)

@router.callback_query(F.data == "ignore_category")
async def ignore_category(callback: CallbackQuery):
    """Заглушка для некликабельных заголовков категорий"""
    print("🔍 НАЖАТ НЕКЛИКАБЕЛЬНЫЙ ЗАГОЛОВОК")
    await callback.answer()

@router.callback_query(F.data == "interests_save")
async def interests_save(callback: CallbackQuery):
    """Сохранение интересов"""
    print("🔍 НАЖАТА КНОПКА: interests_save")
    # Этот обработчик будет переопределен в registration.py и profile.py
    await callback.answer()

@router.callback_query(F.data == "interests_back")
async def interests_back(callback: CallbackQuery):
    """Назад"""
    print("🔍 НАЖАТА КНОПКА: interests_back")
    # Этот обработчик будет переопределен в registration.py и profile.py
    await callback.answer()