# 6 категорий для мероприятий
EVENT_CATEGORIES = [
    "🎨 Творчество",
    "💬 Общение",
    "🏃‍♀️ Активности",
    "🎬 Развлечения",
    "💄 Красота и здоровье",
    "📚 Образование и развитие"
]

def get_categories_keyboard():
    """Создает клавиатуру с 6 категориями"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    for category in EVENT_CATEGORIES:
        builder.button(text=category, callback_data=f"cat_{category}")
    builder.adjust(2)
    return builder.as_markup()