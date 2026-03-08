FROM python:3.11.9-slim

WORKDIR /app

# Сначала копируем только файл с зависимостями
COPY requirements.txt .

# Убедимся, что файл скопирован (для отладки)
RUN echo "=== СОДЕРЖИМОЕ REQUIREMENTS.TXT ===" && cat requirements.txt && echo "=== КОНЕЦ ==="

# Обновляем pip и устанавливаем зависимости с подробным выводом
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -v -r requirements.txt

# Проверяем, что библиотеки реально установились
RUN python -c "import aiogram; print('✅ aiogram установлен!')"

# Копируем остальной код
COPY . .

CMD ["python", "bot.py"]