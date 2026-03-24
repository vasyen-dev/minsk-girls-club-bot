from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

def create_calendar(year: int = None, month: int = None):
    """Создает календарь для выбора даты"""
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
    
    # Заголовок: месяц и год
    builder.append([
        InlineKeyboardButton(text="◀️", callback_data=f"cal_prev_{year}_{month}"),
        InlineKeyboardButton(text=f"{month_names[month-1]} {year}", callback_data="ignore"),
        InlineKeyboardButton(text="▶️", callback_data=f"cal_next_{year}_{month}")
    ])
    
    # Дни недели
    week_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    row = []
    for day in week_days:
        row.append(InlineKeyboardButton(text=day, callback_data="ignore"))
    builder.append(row)
    
    # Первый день месяца
    first_day = datetime(year, month, 1)
    start_weekday = first_day.weekday()  # 0 = понедельник
    
    # Количество дней в месяце
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    days_in_month = (next_month - first_day).days
    
    row = []
    # Пустые ячейки до первого дня
    for _ in range(start_weekday):
        row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
    
    for day in range(1, days_in_month + 1):
        date = datetime(year, month, day)
        # Не показываем прошедшие даты
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

def create_hour_keyboard():
    """Создает клавиатуру для выбора часа (все 24 часа)"""
    builder = []
    row = []
    for hour in range(0, 24):
        row.append(InlineKeyboardButton(text=f"{hour:02d}:00", callback_data=f"hour_{hour}"))
        if len(row) == 4:
            builder.append(row)
            row = []
    if row:
        builder.append(row)
    
    builder.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_calendar"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_date")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=builder)

def create_minute_keyboard(hour):
    """Создает клавиатуру для выбора минут (00, 15, 30, 45)"""
    minutes = ["00", "15", "30", "45"]
    
    builder = []
    row = []
    for minute in minutes:
        # callback_data: minute_20_30 (где 20 - час, 30 - минута)
        row.append(InlineKeyboardButton(text=f"{minute}", callback_data=f"minute_{hour}_{minute}"))
    builder.append(row)
    
    builder.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_hour"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_date")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=builder)