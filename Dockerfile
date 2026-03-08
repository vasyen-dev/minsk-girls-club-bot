FROM python:3.11.9-slim

WORKDIR /app

# Копируем только requirements.txt сначала (для кэширования)
COPY requirements.txt .

# Принудительно обновляем pip и устанавливаем с verbose-выводом
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -v -r requirements.txt

# Добавляем проверку, что библиотеки реально установились
RUN python -c "import aiogram; print('✅ aiogram installed successfully')" || (echo '❌ aiogram NOT installed' && exit 1)

# Копируем остальной код
COPY . .

CMD ["python", "bot.py"]