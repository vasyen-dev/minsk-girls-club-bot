from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

def create_date_time_keyboard():
    """Создает клавиатуру с готовыми вариантами дат"""
    now = datetime.now()
    
    dates = [
        (now + timedelta(days=1), "Завтра"),
        (now + timedelta(days=2), "Послезавтра"),
        (now + timedelta(days=3), f"{now.strftime('%d.%m')}"),
        (now + timedelta(days=4), f"{now.strftime('%d.%m')}"),
        (now + timedelta(days=5), f"{now.strftime('%d.%m')}"),
        (now + timedelta(days=6), f"{now.strftime('%d.%m')}"),
        (now + timedelta(days=7), "Через неделю"),
    ]
    
    builder = []
    
    for date, label in dates:
        day = date.strftime('%d.%m')
        if label == "Завтра":
            day_label = f"📅 Завтра ({day})"
        elif label == "Послезавтра":
            day_label = f"📅 Послезавтра ({day})"
        elif label == "Через неделю":
            day_label = f"📅 Через неделю ({day})"
        else:
            day_label = f"📅 {day}"
        
        builder.append([
            InlineKeyboardButton(text=day_label, callback_data=f"date_{date.year}_{date.month}_{date.day}")
        ])
    
    builder.append([
        InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="manual_date")
    ])
    
    builder.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_date")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=builder)

def create_time_keyboard_for_date(selected_date):
    """Создает клавиатуру с вариантами времени для выбранной даты"""
    # Варианты времени с шагом 30 минут
    times = [
        "10:00", "10:30", "11:00", "11:30",
        "12:00", "12:30", "13:00", "13:30",
        "14:00", "14:30", "15:00", "15:30",
        "16:00", "16:30", "17:00", "17:30",
        "18:00", "18:30", "19:00", "19:30",
        "20:00", "20:30", "21:00"
    ]
    
    builder = []
    row = []
    for time in times:
        row.append(InlineKeyboardButton(text=f"🕒 {time}", callback_data=f"time_{time}"))
        if len(row) == 3:
            builder.append(row)
            row = []
    if row:
        builder.append(row)
    
    builder.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_dates"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_date")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=builder)