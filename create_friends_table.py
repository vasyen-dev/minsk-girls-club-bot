# create_friends_table.py
from database.models import Base, Friend
from database.requests import engine

print("Создаем таблицу friends...")
Base.metadata.create_all(engine)
print("Готово!")