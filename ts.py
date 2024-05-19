import os
import string
import secrets
import logging
import zipfile
import requests
from github import Github
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler

# إعدادات السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# المتغيرات الأساسية
TELEGRAM_TOKEN = "7046309155:AAH0f4ObaNcExF23RDQmrJJcjvkijQ4tae0"
GITHUB_TOKEN = "YOUR_GITHUB_TOKEN"
HEROKU_API_KEY = "YOUR_HEROKU_API_KEY"
ADMIN_ID = "YOUR_ADMIN_ID"
PASSWORD = "محمد تناحه"

# الدوال المساعدة
def get_github_repos() -> list:
    g = Github(GITHUB_TOKEN)
    user = g.get_user()
    return [repo.name for repo in user.get_repos()]

def get_heroku_apps() -> list:
    headers = {
        "Authorization": f"Bearer {HEROKU_API_KEY}",
        "Accept": "application/vnd.heroku+json; version=3"
    }
    response = requests.get("https://api.heroku.com/apps", headers=headers)
    return [app['name'] for app in response.json()] if response.status_code == 200 else []

def delete_github_repo(name: str) -> bool:
    g = Github(GITHUB_TOKEN)
    user = g.get_user()
    try:
        repo = user.get_repo(name)
        repo.delete()
        return True
    except Exception:
        return False

def delete_heroku_app(name: str) -> bool:
    headers = {
        "Authorization": f"Bearer {HEROKU_API_KEY}",
        "Accept": "application/vnd.heroku+json; version=3"
    }
    response = requests.delete(f"https://api.heroku.com/apps/{name}", headers=headers)
    return response.status_code == 202

def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id != int(ADMIN_ID):
        update.message.reply_text("يرجى إدخال كلمة المرور.")
        return

    welcome_message = "أهلاً بك! يمكنك إدارة المستودعات والخوادم باستخدام الأزرار أدناه."
    keyboard = [
        [InlineKeyboardButton("عرض مستودعات GitHub", callback_data='show_github_repos')],
        [InlineKeyboardButton("عرض خوادم Heroku", callback_data='show_heroku_apps')],
        [InlineKeyboardButton("إنشاء مستودع جديد", callback_data='create_github_repo')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(welcome_message, reply_markup=reply_markup)

def authenticate(update: Update, context: CallbackContext) -> None:
    password = update.message.text
    if password == PASSWORD:
        context.user_data['authenticated'] = True
        update.message.reply_text("تم التحقق من كلمة المرور بنجاح، ارسل /start للبدء.")
    else:
        update.message.reply_text("كلمة المرور غير صحيحة. يرجى المحاولة مرة أخرى.")

def create_github_repo(update: Update, context: CallbackContext) -> None:
    if 'authenticated' not in context.user_data:
        update.message.reply_text("يرجى إدخال كلمة المرور أولاً.")
        return

    file = update.message.document
    if not file or not file.file_name.endswith('.zip'):
        update.message.reply_text("يرجى إرسال ملف مضغوط (ZIP).")
        return

    file_name = file.file_name
    file_path = f"./{file_name}"
    file.get_file().download(file_path)

    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(f"./{file_name[:-4]}")
    except Exception as e:
        update.message.reply_text("حدث خطأ أثناء فك الضغط على الملف.")
        logging.error(f"Error extracting ZIP file: {e}")
        return

    random_string = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(2))
    repo_name = f"{update.effective_user.username}-{random_string}-repo"
    g = Github(GITHUB_TOKEN)
    user = g.get_user()

    try:
        repo = user.create_repo(repo_name, private=True)
        for root, dirs, files in os.walk(f"./{file_name[:-4]}"):
            for file in files:
                with open(os.path.join(root, file), 'rb') as f:
                    content = f.read()
                    repo.create_file(os.path.relpath(os.path.join(root, file), f"./{file_name[:-4]}"), f"Add {file}", content)
        files_count = sum(len(files) for _, _, files in os.walk(f"./{file_name[:-4]}"))
        success_message = (f"تم إنشاء المستودع بنجاح.\n"
                           f"اسم المستودع: `{repo_name}`\n"
                           f"عدد الملفات: {files_count}")
        update.message.reply_text(success_message, reply_markup=ReplyKeyboardRemove(), parse_mode='Markdown')
    except Exception as e:
        update.message.reply_text("حدث خطأ أثناء إنشاء المستودع.")
        logging.error(f"Error creating GitHub repository: {e}")

    os.remove(file_path)
    os.system(f"rm -rf ./{file_name[:-4]}")

def button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if query.data == 'show_github_repos':
        repos = get_github_repos()
        if repos:
            buttons = [[InlineKeyboardButton(repo, callback_data=f'delete_github_repo_{repo}')] for repo in repos]
            buttons.append([InlineKeyboardButton("رجوع", callback_data='back')])
            query.edit_message_text("الرجاء اختيار المستودع الذي تريد حذفه:", reply_markup=InlineKeyboardMarkup(buttons))
        else:
            query.edit_message_text("لا توجد مستودعات متاحة حالياً على GitHub.")
    elif query.data == 'show_heroku_apps':
        apps = get_heroku_apps()
        if apps:
            buttons = [[InlineKeyboardButton(app, callback_data=f'delete_heroku_app_{app}')] for app in apps]
            buttons.append([InlineKeyboardButton("رجوع", callback_data='back')])
            query.edit_message_text("الرجاء اختيار الخادم الذي تريد حذفه:", reply_markup=InlineKeyboardMarkup(buttons))
        else:
            query.edit_message_text("لا توجد خوادم متاحة حالياً على Heroku.")
    elif query.data == 'create_github_repo':
        query.edit_message_text("يرجى إرسال ملف مضغوط (ZIP) لإنشاء مستودع جديد.")
    elif query.data.startswith('delete_github_repo_'):
        repo_name = query.data[len('delete_github_repo_'):]
        if delete_github_repo(repo_name):
            query.edit_message_text(f"تم حذف المستودع {repo_name} بنجاح.")
        else:
            query.edit_message_text(f"فشل في حذف المستودع {repo_name}.")
    elif query.data.startswith('delete_heroku_app_'):
        app_name = query.data[len('delete_heroku_app_'):]
        if delete_heroku_app(app_name):
            query.edit_message_text(f"تم حذف الخادم {app_name} بنجاح.")
        else:
            query.edit_message_text(f"فشل في حذف الخادم {app_name}.")
    elif query.data == 'back':
        start(update.callback_query.message, context)

def main() -> None:
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_click))
    dp.add_handler(MessageHandler(Filters.text & Filters.private & ~Filters.command, authenticate))
    dp.add_handler(MessageHandler(Filters.document & Filters.private, create_github_repo))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
