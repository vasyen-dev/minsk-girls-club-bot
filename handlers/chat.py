from aiogram import Router, F
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import CLUB_CHAT_LINK

router = Router()

@router.message(F.text == "💬 Чат клуба")
async def cmd_club_chat(message: Message):
    """Показать информацию о чате клуба"""
    
    # Проверяем, есть ли ссылка на чат в конфиге
    if not CLUB_CHAT_LINK:
        await message.answer(
            "💬 *Чат клуба*\n\n"
            "Скоро здесь появится ссылка на общий чат! 🌸",
            parse_mode="Markdown"
        )
        return
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔗 Перейти в чат", url=CLUB_CHAT_LINK)
    
    await message.answer(
        "💬 *Чат клуба SVOI Minsk Girls*\n\n"
        "Здесь ты можешь:\n"
        "• Общаться с другими участницами\n"
        "• Делиться впечатлениями о мероприятиях\n"
        "• Предлагать новые идеи\n"
        "• Находить подруг по интересам\n\n"
        "Ждём тебя в нашем уютном чатике! 🌸",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )