import telebot
import subprocess
import os
import zipfile
import tempfile
import shutil
import requests
import re
import logging
from telebot import types
import time
import psycopg2

TOKEN = '7907373169:AAE-KqIlyhZLcXd2iWyEbBTiHCDGElM6J_s'  # ضع هنا توكن البوت الخاص بك
ADMIN_ID = 7072622935  # ضع هنا معرف الأدمن الخاص بك
CHANNEL = '@Viptofey'  # ضع هنا معرف القناة الخاصة بك

bot = telebot.TeleBot(TOKEN)
uploaded_files_dir = 'uploaded_bots'
bot_scripts = {}

if not os.path.exists(uploaded_files_dir):
    os.makedirs(uploaded_files_dir)

DATABASE_URL = "postgres://user:password@host:port/dbname"  # ضع هنا رابط قاعدة البيانات الخاص بك
connection = psycopg2.connect(DATABASE_URL, sslmode='require')
cursor = connection.cursor()

def initialize_database():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            is_subscribed BOOLEAN DEFAULT FALSE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            file_id SERIAL PRIMARY KEY,
            user_id BIGINT,
            file_name TEXT,
            file_path TEXT,
            is_running BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)
    connection.commit()

def check_subscription(user_id):
    try:
        member_status = bot.get_chat_member(CHANNEL, user_id).status
        is_subscribed = member_status in ['member', 'administrator', 'creator']
        cursor.execute("INSERT INTO users (user_id, username, is_subscribed) VALUES (%s, %s, %s) ON CONFLICT (user_id) DO UPDATE SET is_subscribed = EXCLUDED.is_subscribed", (user_id, bot.get_chat(user_id).username, is_subscribed))
        connection.commit()
        return is_subscribed
    except telebot.apihelper.ApiException as e:
        if "Bad Request: member list is inaccessible" in str(e):
            bot.send_message(ADMIN_ID, "⚠️ لا يمكن الوصول إلى قائمة الأعضاء في القناة. يرجى التأكد من أن البوت مشرف (Admin) في القناة.")
        logging.error(f"Error checking subscription: {e}")
        return False

def ask_for_subscription(chat_id):
    markup = types.InlineKeyboardMarkup()
    join_button = types.InlineKeyboardButton('اشترك في القناة', url=f'https://t.me/{CHANNEL}')
    markup.add(join_button)
    bot.send_message(chat_id, f"عزيزي المستخدم، عليك الاشتراك في القناة {CHANNEL} لتتمكن من استخدام البوت.", reply_markup=markup)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id

    if not check_subscription(user_id):
        ask_for_subscription(message.chat.id)
        return

    markup = types.InlineKeyboardMarkup()
    upload_button = types.InlineKeyboardButton('رفع ملف بوت', callback_data='upload')
    running_files_button = types.InlineKeyboardButton('عرض الملفات قيد التشغيل', callback_data='running_files')
    dev_channel_button = types.InlineKeyboardButton('قناة المطور', url='https://t.me/M1telegramM1')
    markup.add(upload_button, running_files_button)
    markup.add(dev_channel_button)
    bot.send_message(message.chat.id, f"مرحباً، {message.from_user.first_name}! يمكنك استخدام الأزرار أدناه للتحكم في الملفات التي قمت برفعها:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'upload')
def ask_to_upload_file(call):
    bot.send_message(call.message.chat.id, "من فضلك، أرسل الملف الذي تريد رفعه. يمكنك تشغيل حتى 5 ملفات.")

@bot.message_handler(content_types=['document'])
def handle_file(message):
    user_id = message.from_user.id

    if not check_subscription(user_id):
        ask_for_subscription(message.chat.id)
        return

    cursor.execute("SELECT COUNT(*) FROM files WHERE user_id = %s", (user_id,))
    file_count = cursor.fetchone()[0]

    if file_count >= 5:
        bot.send_message(message.chat.id, "لقد وصلت إلى الحد الأقصى لعدد الملفات التي يمكنك تشغيلها (5 ملفات).")
        return

    try:
        file_id = message.document.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_name = message.document.file_name

        if not file_name.endswith('.py'):
            bot.reply_to(message, "يرجى إرسال ملفات بايثون فقط.")
            return

        script_path = os.path.join(uploaded_files_dir, f"{user_id}_{file_name}")
        with open(script_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        run_script(script_path, message.chat.id, file_name, message)

    except Exception as e:
        bot.reply_to(message, f"حدث خطأ: {e}")

def run_script(script_path, chat_id, file_name, original_message):
    try:
        requirements_path = os.path.join(os.path.dirname(script_path), 'requirements.txt')
        if os.path.exists(requirements_path):
            bot.send_message(chat_id, "جارٍ تثبيت المتطلبات...")
            subprocess.check_call(['pip', 'install', '-r', requirements_path])

        bot.send_message(chat_id, f"جارٍ تشغيل البوت {file_name}...")
        process = subprocess.Popen(['python3', script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        bot_scripts[chat_id] = {'process': process}

        cursor.execute("INSERT INTO files (user_id, file_name, file_path, is_running) VALUES (%s, %s, %s, %s)", (original_message.from_user.id, file_name, script_path, True))
        connection.commit()

        bot.send_message(chat_id, f"تم تشغيل البوت {file_name} بنجاح!")

    except Exception as e:
        bot.send_message(chat_id, f"حدث خطأ أثناء تشغيل البوت: {e}")

@bot.callback_query_handler(func=lambda call: call.data == 'running_files')
def show_running_files(call):
    user_id = call.from_user.id
    cursor.execute("SELECT file_name FROM files WHERE user_id = %s AND is_running = TRUE", (user_id,))
    files = cursor.fetchall()

    if not files:
        bot.send_message(call.message.chat.id, "لا توجد ملفات قيد التشغيل حالياً.")
        return

    markup = types.InlineKeyboardMarkup()
    for file in files:
        file_name = file[0]
        markup.add(types.InlineKeyboardButton(file_name, callback_data=f'stop_{file_name}'))

    bot.send_message(call.message.chat.id, "الملفات قيد التشغيل:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('stop_'))
def stop_and_delete_file(call):
    user_id = call.from_user.id
    file_name = call.data.split('_', 1)[1]

    cursor.execute("SELECT file_path FROM files WHERE user_id = %s AND file_name = %s", (user_id, file_name))
    file_path = cursor.fetchone()

    if file_path and os.path.exists(file_path[0]):
        # إيقاف العملية إذا كانت قيد التشغيل
        if user_id in bot_scripts and bot_scripts[user_id]['process']:
            bot_scripts[user_id]['process'].terminate()
            del bot_scripts[user_id]

        os.remove(file_path[0])
        cursor.execute("DELETE FROM files WHERE user_id = %s AND file_name = %s", (user_id, file_name))
        connection.commit()
        bot.send_message(call.message.chat.id, f"تم إيقاف وحذف الملف {file_name}.")
    else:
        bot.send_message(call.message.chat.id, "لم يتم العثور على الملف.")

initialize_database()
bot.infinity_polling()
