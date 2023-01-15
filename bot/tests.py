from django.test import TestCase
import sqlite3

# Create your tests here.
conn = sqlite3.connect('Database.db')
cursor = conn.cursor()
cursor.execute("SELECT openai_api, telegram_api FROM bot_data_api WHERE id = 1")
openai_api, telegram_api = cursor.fetchone()
print(openai_api)
print(telegram_api)