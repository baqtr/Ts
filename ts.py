import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
import subprocess
import os
import threading
import time
import ast
import sys

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = "7046309155:AAH0f4ObaNcExF23RDQmrJJcjvkijQ4tae0"

user_files = {}
lock = threading.Lock()
MAX_FILES_PER_USER = 5
FILE_EXPIRY_TIME = 3600  # 1 hour

def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    if user_id in user_files:
        for file_info in user_files[user_id]['files']:
            file_path = file_info['path']
            if os.path.exists(file_path):
                os.remove(file_path)
        del user_files[user_id]

    user_files.setdefault(user_id, {'files': [], 'expiry_time': 0, 'last_result': ''})
    
    total_users = len(user_files)

    welcome_message = f"مرحباً بك في بوت استضافة البايثون. يمكنك إرسال ملف بايثون وسنقوم بتشغيله لك. إذا كان هناك أي أخطاء، سنعلمك بها. عدد المستخدمين الحالي: {total_users}.\n\nاستخدم الأزرار أدناه للتحكم:"
    keyboard = [
        [InlineKeyboardButton("عرض المعلومات", callback_data='info')],
        [InlineKeyboardButton("حفظ النسخة الاحتياطية", callback_data='backup')],
        [InlineKeyboardButton("استعادة النسخة الاحتياطية", callback_data='restore')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(welcome_message, reply_markup=reply_markup)

def handle_file(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_files.setdefault(user_id, {'files': [], 'expiry_time': 0, 'last_result': ''})

    if len(user_files[user_id]['files']) >= MAX_FILES_PER_USER:
        update.message.reply_text("لقد تجاوزت الحد الأقصى لعدد الملفات المسموح بها. الرجاء المحاولة مرة أخرى لاحقًا.")
        return

    user_file = update.message.document
    file_name = user_file.file_name

    if not file_name.endswith('.py'):
        update.message.reply_text("الرجاء إرسال ملف بايثون فقط.")
        return

    file_id = user_file.file_id
    file_path = f"{user_id}_{file_name}"
    user_file.get_file().download(file_path)

    user_files[user_id]['files'].append({'path': file_path, 'start_time': 0, 'expiry_time': time.time() + FILE_EXPIRY_TIME, 'last_result': ''})

    update.message.reply_text("تم استلام الملف، سيتم تشغيله قريباً ✅")

    thread = threading.Thread(target=run_python_file, args=(update, user_id, len(user_files[user_id]['files']) - 1))
    thread.start()

def run_python_file(update: Update, user_id: int, file_index: int) -> None:
    try:
        with lock:
            file_info = user_files[user_id]['files'][file_index]
            file_path = file_info['path']
            user_files[user_id]['files'][file_index]['start_time'] = time.time()

        with open(file_path, 'r') as f:
            code = f.read()

        try:
            # Check syntax errors
            ast.parse(code)
        except SyntaxError as e:
            message = f"فشل تشغيل الملف بسبب خطأ نحوي ❌:\n\n{str(e)}"
        else:
            result = subprocess.run([sys.executable, file_path], capture_output=True, text=True)

            if result.returncode == 0:
                message = f"تم تشغيل الملف ({file_index + 1}) بنجاح ✅:\n\n{result.stdout}"
            else:
                message = f"فشل تشغيل الملف ({file_index + 1}) ❌:\n\n{result.stderr}"

        with lock:
            user_files[user_id]['files'][file_index]['last_result'] = message
        update.message.reply_text(message)

    except Exception as e:
        with lock:
            user_files[user_id]['files'][file_index]['last_result'] = f"حدث خطأ أثناء التشغيل:\n\n{str(e)}"
        update.message.reply_text(f"حدث خطأ أثناء التشغيل:\n\n{str(e)}")

    finally:
        with lock:
            os.remove(file_path)

def cleanup_expired_files():
    while True:
        time.sleep(60)
        with lock:
            for user_id in list(user_files.keys()):
                user_files[user_id]['files'] = [f for f in user_files[user_id]['files'] if time.time() < f['expiry_time']]
                if not user_files[user_id]['files']:
                    del user_files[user_id]

def history(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    if user_id not in user_files or not user_files[user_id]['files']:
        update.message.reply_text("لا يوجد سجل تشغيل للعرض.")
        return

    history_message = "سجل التشغيل:\n\n"
    for i, file_info in enumerate(user_files[user_id]['files'], 1):
        history_message += f"ملف {i}:\n{file_info['last_result']}\n\n"
    
    update.message.reply_text(history_message)

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()

    if query.data == 'info':
        if user_id not in user_files or not user_files[user_id]['files']:
            query.edit_message_text("لا توجد ملفات قيد التشغيل.")
            return

        info_message = "معلومات التشغيل:\n\n"
        for i, file_info in enumerate(user_files[user_id]['files'], 1):
            elapsed_time = time.time() - file_info['start_time']
            info_message += f"ملف {i}:\nالوقت المستغرق: {elapsed_time:.2f} ثانية\n\n"
        
        query.edit_message_text(info_message)

    elif query.data == 'backup':
        backup_data = {'user_files': user_files}
        with open('backup.json', 'w') as backup_file:
            json.dump(backup_data, backup_file)
        query.edit_message_text("تم حفظ النسخة الاحتياطية بنجاح ✅")

    elif query.data == 'restore':
        try:
            with open('backup.json', 'r') as backup_file:
                backup_data = json.load(backup_file)
            global user_files
            user_files = backup_data['user_files']
            query.edit_message_text("تم استعادة النسخة الاحتياطية بنجاح ✅")
        except FileNotFoundError:
            query.edit_message_text("لم يتم العثور على ملف النسخة الاحتياطية ❌")
        except Exception as e:
            query.edit_message_text(f"حدث خطأ أثناء استعادة النسخة الاحتياطية ❌:\n\n{str(e)}")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("history", history))
    dp.add_handler(MessageHandler(Filters.document & Filters.private, handle_file))
    dp.add_handler(CallbackQueryHandler(button))

    cleanup_thread = threading.Thread(target=cleanup_expired_files, daemon=True)
    cleanup_thread.start()

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
