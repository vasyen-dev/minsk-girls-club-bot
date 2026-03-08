FROM python:3.11.9-slim

WORKDIR /app

# Копируем только requirements.txt сначала
COPY requirements.txt .

# Принудительно обновляем pip и устанавливаем зависимости с verbose-выводом
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -v -r requirements.txt

# Копируем остальной код
COPY . .

CMD ["python", "bot.py"]