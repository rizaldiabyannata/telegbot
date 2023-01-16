import telebot
from telebot import util
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import openai
import sqlite3
import pytz
import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
import time
import requests

scheduler = BlockingScheduler(timezone=pytz.timezone('Asia/Makassar'))

conn = sqlite3.connect('Database.db')
cursor = conn.cursor()
cursor.execute("SELECT openai_api, telegram_api, chatId_telegram FROM bot_data_api WHERE id = 1")
openai_api, telegram_api, chat_id = cursor.fetchone()
openai.api_key = openai_api
bot = telebot.TeleBot(telegram_api)

def respon(question):
    prmt = "Q: {qst}\nA:".format(qst=question)
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prmt,
        temperature=1,
        max_tokens=4000,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )
    return response.choices[0].text


@bot.message_handler(commands=['help'])
def send_welcome(message):
    bot.send_message(
        message.chat.id, 'gunakan /ask untuk bertannya \nJika membuat jadwal gunakan /extract dengan format /extract\nMatkul: xxxxxxx \nDeadline: YYYY-MM-DD HH:MM \nKeterangan: xxxxxxxxxxx')
    
@bot.message_handler(func=lambda message: True, commands=["ask"])
def echo_message(message):
    msg = message.text
    response = respon(msg)
    bot.send_message(message.chat.id, response)
    
def delete_expired_tasks():
    threshold_time = datetime.datetime.now() - datetime.timedelta(days=2)
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bot_scheduler WHERE Dateline < ?", (threshold_time,))
    conn.commit()
    conn.close()

def send_message_reminder(task_name, deadline, descrip):
    message = f'Reminder: kamu ada tugas yang belum dikerjakan\nMjatkul: {task_name}\nDeadline: {deadline}\nKet: {descrip}'
    bot.send_message(chat_id, text=message)

def schedule_reminders(task_name, deadline, descrip, process):
    current_time = datetime.datetime.now()
    reminder_time = current_time + datetime.timedelta(minutes=5)
    while reminder_time < deadline and process == 0 : 
        
        if reminder_time > deadline - datetime.timedelta(hours=2):
            interval = datetime.timedelta(minutes=1)
        else:
            interval = datetime.timedelta(minutes=5)
        scheduler.add_job(send_message_reminder, 'date', run_date=reminder_time, args=[task_name, deadline, descrip])
        reminder_time += interval
    
def schedule_reminders_from_database():
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bot_scheduler")
    rows = cursor.fetchall()
    for row in rows:
        task_name = row[1]
        try:
            deadline = datetime.datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            deadline_str = row[2] + ":00"
            deadline = datetime.datetime.strptime(deadline_str, '%Y-%m-%d %H:%M:%S')
        descrip = row[3]
        process = row[4]
        print(task_name,descrip,deadline,process)
        schedule_reminders(task_name, deadline, descrip, process)
            
@bot.message_handler(commands=["remainder"])
def handle_reminder_command(message):
    schedule_reminders_from_database()
    if len(scheduler.get_jobs()) > 0:
        bot.send_message(message.chat.id, text="Pengingat telah dijadwalkan.")
        scheduler.start()
    else:
        bot.send_message(message.chat.id, text="Tidak ada tugas yang harus diselesaikan")
        
@bot.message_handler(commands=['extract'])
def extract_data(message):
    fields = message.text.split('\n')
    matkul = fields[1].split(': ')[1]
    deadline_str = fields[2].split(': ')[1].strip()
    keterangan = fields[3].split(': ')[1]
    deadline = datetime.datetime.strptime(deadline_str, '%Y-%m-%d %H:%M:%S')
    print(fields)
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO bot_scheduler (Matkul, Dateline, Keterangan, Status) VALUES (?, ?, ?, ?)
    ''', (matkul, deadline, keterangan, 0))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "Extract berhasil dilakukan")
    print("Data successfully extracted and stored in the database.")
    if scheduler.get_jobs():
        scheduler.remove_all_jobs()
        scheduler.shutdown()
        handle_reminder_command(message)
    else:
        handle_reminder_command(message)
        
@bot.message_handler(commands=["stop"])
def handle_pause_reminder(message):
    scheduler.shutdown()
    scheduler.remove_all_jobs()
    bot.send_message(message.chat.id, "Remainder berhenti")

@bot.message_handler(commands=["delete_expired"])
def delete_data_from_database(message):
    delete_expired_tasks()
    bot.send_message(message.chat.id, "data expired telah berhasil dihapus")
    print("data remainder telah dihapus")

def keyboard_markup(matkul):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("Sudah dikerjakan", callback_data=matkul))
    return markup

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    cursor.execute(
        "UPDATE bot_scheduler SET Status = 1 WHERE Matkul = ?", (call.data,))
    conn.commit()
    conn.close()
    bot.answer_callback_query(call.id, f"Tugas {call.id} Sudah dikerjakan")
    print(
        f"Tugas pada matkul {call.data} telah diselesaikan dan database telah diupdate")
    bot.send_message(call.id, f"Tugas pada matkul {call.data} telah diselesaikan dan database telah diupdate")

@bot.message_handler(func=lambda message: True, commands=["list_tasks"])
def list_task(message):
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT Matkul, Dateline, Keterangan FROM bot_scheduler")
    rows = cursor.fetchall()
    for row in rows:
        matkul = row[0]
        deadline = row[1]
        keterangan = row[2]
        print(f"Matkul: {matkul}")
        print(f"Dateline: {deadline}")
        print(f"Keterangan: {keterangan}")
        bot.send_message(
            message.chat.id, f"Matkul: {matkul}\nDeadline: {deadline}\nKeterangan: {keterangan}", reply_markup=keyboard_markup(matkul))

@bot.message_handler(func=lambda message: True, commands=["delete"])
def delete_select_task(message):
    task_names = message.text.split()[1:]
    try:
        conn = sqlite3.connect('Database.db')
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM bot_scheduler WHERE Matkul = ?", (task_names))
        bot.send_message(message.chat.id, f"Tugas {task_names} telah dihapus")
        conn.commit()
        conn.close()
    except Exception as e:
        bot.send_message(
            message.chat.id, f"Tugas {task_names} tidak terhapus (terjadi error : {e})")

@bot.message_handler(commands=["weather"])
def check_weather(message):
        city = message.text.split()[1]
        bot.send_message(
        message.chat.id, f"_Looking for details of_ {city}...", parse_mode="Markdown"
        )
        query = (
            f"http://api.openweathermap.org/data/2.5/weather?q={city}"
            f"&appid=aaced31d1985dc0feac4d5bb1aa51ea2"
        )
        response = requests.get(query)
        if response.status_code == 200:
            res = response.json()
            temp = round((res["main"]["temp_min"] - 273.15), 2)
            pressure = round(res["main"]["pressure"] - 1013.15)
            rise = datetime.fromtimestamp(res["sys"]["sunrise"])
            set = datetime.fromtimestamp(res["sys"]["sunset"])
            bot.send_message(
            message.chat.id,
            f"**** {res['name']} ****\nTemperature: {temp}°C\n"
            f"Humidity: {res['main']['humidity']}%\nWeather: {res['weather'][0]['description']}\n"
            f"Pressure: {pressure} atm\nSunrise: {rise.strftime('%I:%M %p')}\n"
            f"Sunset: {set.strftime('%I:%M %p')}\nCountry: {res['sys']['country']}"
            )
        else:
            bot.send_message(message.chat.id, "Sorry, I could not find information for that city.")
   
def run_bot():
    while True:
        try:
            print('bot start running')
            bot.polling()
        except Exception as e:
            print(e)
            bot.send_message(chat_id, text = f"{e}" )
            bot.stop_polling
            time.sleep(5)
    
            