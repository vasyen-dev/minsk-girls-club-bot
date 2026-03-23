from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

def create_date_time_keyboard():
    """Создает клавиатуру с готовыми вариантами дат"""
    now = datetime.now()
    
    # Готовые варианты дат
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
    
    # Кнопки с датами
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
    
    # Кнопка для ручного ввода
    builder.append([
        InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="manual_date")
    ])
    
    builder.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_date")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=builder)

def create_time_keyboard_for_date(selected_date):
    """Создает клавиатуру с вариантами времени для выбранной даты"""
    times = [
        ("10:00", "10:00"),
        ("11:00", "11:00"),
        ("12:00", "12:00"),
        ("13:00", "13:00"),
        ("14:00", "14:00"),
        ("15:00", "15:00"),
        ("16:00", "16:00"),
        ("17:00", "17:00"),
        ("18:00", "18:00"),
        ("19:00", "19:00"),
        ("20:00", "20:00"),
        ("21:00", "21:00"),
    ]
    
    builder = []
    row = []
    for time_label, time_value in times:
        row.append(InlineKeyboardButton(text=f"🕒 {time_label}", callback_data=f"time_{time_value}"))
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

def create_calendar(year: int = None, month: int = None):
    """Создает календарь для ручного выбора (если понадобится)"""
    now = datetime.now()
    if year is None:
        year = now.year
    if month is None:
        month = now.month
    
    month_names = [
        "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]
    
    builder = []
    
    builder.append([
        InlineKeyboardButton(text="◀️", callback_data=f"cal_prev_{year}_{month}"),
        InlineKeyboardButton(text=f"{month_names[month-1]} {year}", callback_data="ignore"),
        InlineKeyboardButton(text="▶️", callback_data=f"cal_next_{year}_{month}")
    ])
    
    week_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    row = []
    for day in week_days:
        row.append(InlineKeyboardButton(text=day, callback_data="ignore"))
    builder.append(row)
    
    first_day = datetime(year, month, 1)
    start_weekday = first_day.weekday()
    
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    days_in_month = (next_month - first_day).days
    
    row = []
    for _ in range(start_weekday):
        row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
    
    for day in range(1, days_in_month + 1):
        date = datetime(year, month, day)
        if date.date() >= datetime.now().date():
            row.append(InlineKeyboardButton(text=str(day), callback_data=f"date_{year}_{month}_{day}"))
        else:
            row.append(InlineKeyboardButton(text=str(day), callback_data="ignore"))
        
        if len(row) == 7:
            builder.append(row)
            row = []
    
    if row:
        while len(row) < 7:
            row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
        builder.append(row)
    
    builder.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_date")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=builder)