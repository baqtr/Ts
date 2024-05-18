import os
import string
import secrets
import logging
import zipfile
import requests
from github import Github
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler, ConversationHandler
from time import sleep
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TELEGRAM_TOKEN = "7046309155:AAH0f4ObaNcExF23RDQmrJJcjvkijQ4tae0"
GITHUB_TOKEN = "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"
HEROKU_API_KEY = "HRKU-47748b92-c786-45b0-8083-b7120cf1f6ba"
ADMIN_ID = "7013440973"

user_count = 0
executor = ThreadPoolExecutor(max_workers=10)

PASSWORD, MAIN_MENU = range(2)

def get_repository_count(github_token: str) -> int:
    g = Github(github_token)
    user = g.get_user()
    repositories = user.get_repos()
    return len(list(repositories))

def get_heroku_apps_count() -> int:
    headers = {
        "Authorization": f"Bearer {HEROKU_API_KEY}",
        "Accept": "application/vnd.heroku+json; version=3"
    }
    response = requests.get("https://api.heroku.com/apps", headers=headers)
    if response.status_code == 200:
        return len(response.json())
    return 0

def get_github_repositories_count() -> int:
    g = Github(GITHUB_TOKEN)
    user = g.get_user()
    repos = user.get_repos()
    return repos.totalCount

def get_heroku_apps() -> list:
    headers = {
        "Authorization": f"Bearer {HEROKU_API_KEY}",
        "Accept": "application/vnd.heroku+json; version=3"
    }
    response = requests.get("https://api.heroku.com/apps", headers=headers)
    if response.status_code == 200:
        return [app['name'] for app in response.json()]
    return []

def get_github_repos() -> list:
    g = Github(GITHUB_TOKEN)
    user = g.get_user()
    repos = user.get_repos()
    return [repo.name for repo in repos]

def delete_heroku_app(name: str) -> bool:
    headers = {
        "Authorization": f"Bearer {HEROKU_API_KEY}",
        "Accept": "application/vnd.heroku+json; version=3"
    }
    response = requests.delete(f"https://api.heroku.com/apps/{name}", headers=headers)
    return response.status_code == 202

def delete_github_repository(name: str) -> bool:
    g = Github(GITHUB_TOKEN)
    user = g.get_user()
    try:
        repo = user.get_repo(name)
        repo.delete()
        return True
    except Exception:
        return False

def start(update: Update, context: CallbackContext) -> int:
    global user_count
    user_id = update.message.from_user.id
    if user_id not in context.user_data:
        update.message.reply_text("يرجاء ارسال كلمة المرور ‼️")
        return PASSWORD

    context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
    welcome_message = f"اهلا نورت ارسل ملف مضغوط zip لرفعه على جيتهاب وتاكد من وضع متطلباته ويمكنك رفع ملف php ~ Python "
    user_count_message = f"عدد المستخدمين: {user_count}"
    repository_count_message = f"عدد المستودعات: {get_repository_count(GITHUB_TOKEN)}"
    bot_link_button = InlineKeyboardButton(text='بوت حذف خادم ~ مستودع ♨️', url='https://t.me/kQNBot')
    telegram_link_button = InlineKeyboardButton(text='المطور موهان ✅', url='https://t.me/XX44G')
    keyboard = [[bot_link_button, telegram_link_button]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(f"{welcome_message}\n\n{user_count_message}\n{repository_count_message}", reply_markup=reply_markup)
    return MAIN_MENU

def authenticate(update: Update, context: CallbackContext) -> None:
    global user_count
    password = update.message.text
    if password == "محمد تناحه":
        user_id = update.message.from_user.id
        context.user_data[user_id] = True
        user_count += 1
        reply_text = "تم قبول كلمة السر الصحيحة، ارسل /start لنبدأ"
        context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
        context.bot.send_message(chat_id=update.effective_chat.id, text=reply_text)
        sleep(3)
        start(update, context)
    else:
        update.message.reply_text("كلمة المرور غير صحيحة. يرجى المحاولة مرة أخرى.")

def create_github_repository(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id not in context.user_data:
        update.message.reply_text("يرجى إدخال كلمة المرور أولاً.")
        return

    if not update.message.document or not update.message.document.file_name.endswith('.zip'):
        update.message.reply_text("يرجى إرسال ملف مضغوط (ZIP).")
        return

    file = update.message.document
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
    
    repository_name = f"{update.effective_user.username}-{random_string}-github-repo"
    g = Github(GITHUB_TOKEN)
    user = g.get_user()

    try:
        repo = user.create_repo(repository_name, private=True)
    except Exception as e:
        update.message.reply_text("حدث خطأ أثناء إنشاء مستودع GitHub.")
        logging.error(f"Error creating GitHub repository: {e}")
        return

    try:
        for root, dirs, files in os.walk(f"./{file_name[:-4]}"):
            for file in files:
                with open(os.path.join(root, file), 'rb') as f:
                    content = f.read()
                    repo.create_file(os.path.join(root, file), f"Add {file}", content)
    except Exception as e:
        update.message.reply_text("حدث خطأ أثناء إضافة الملفات إلى المستودع.")
        logging.error(f"Error adding files to GitHub repository: {e}")
        return

    files_count = sum(len(files) for _, _, files in os.walk(f"./{file_name[:-4]}"))

    success_emoji = "\U0001F389"
    copy_emoji = "\U0001F4CC"
    repository_link = f"`{repository_name}`"
    success_message = (f"الى موهان لكي يقوم بتشغيله لك : @XX44G {success_emoji}\n\n"
                       f"اسم المستودع: {repository_link} - {copy_emoji} انقر لنسخ الاسم\n"
                       f"عدد الملفات التي تم وضوعها في المستودع: {files_count}\n")
    update.message.reply_text(success_message, reply_markup=ReplyKeyboardRemove(), parse_mode='Markdown')

    os.remove(file_path)
    os.system(f"rm -rf ./{file_name[:-4]}")

def verify_password(update: Update, context: CallbackContext) -> int:
    password = update.message.text.strip()
    if password == "محمد تناحه":
        heroku_apps_count = get_heroku_apps_count()
        github_repos_count = get_github_repositories_count()

        update.message.reply_text(
            f"مرحبًا {update.message.from_user.first_name}!\n\n"
            f"الخوادم التي يتم تشغيلها ✅ حاليًا على VPS: {heroku_apps_count}\n"
            f"المستودعات ✅ حاليًا على GitHub: {github_repos_count}\n\n"
            "يمكنك حذف مستودع أو خادم عن طريق النقر على الزر المناسب.",
            reply_markup=get_main_keyboard()
        )
        return MAIN_MENU
    else:
        update.message.reply_text("كلمة المرور غير صحيحة. يرجى المحاولة مرة أخرى.")
        return PASSWORD

def get_main_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("عرض الخوادم VPS", callback_data='heroku_apps')],
        [InlineKeyboardButton("عرض مستودعات GitHub", callback_data='github_repos')],
    ]
    return InlineKeyboardMarkup(keyboard)

def button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if query.data == 'heroku_apps':
        apps_list = get_heroku_apps()
        if apps_list:
            buttons = [[InlineKeyboardButton(app, callback_data=f'heroku_app_{app}')] for app in apps_list]
            buttons.append([InlineKeyboardButton("رجوع", callback_data='back')])
            reply_markup = InlineKeyboardMarkup(buttons)
            query.edit_message_text("الرجاء اختيار الخادم الذي تريد حذفه:", reply_markup=reply_markup)
        else:
            query.edit_message_text("لا توجد خوادم متاحة حاليًا على VPS.")

    elif query.data == 'github_repos':
        repos_list = get_github_repos()
        if repos_list:
            buttons = [[InlineKeyboardButton(repo, callback_data=f'github_repo_{repo}')] for repo in repos_list]
            buttons.append([InlineKeyboardButton("رجوع", callback_data='back')])
            reply_markup = InlineKeyboardMarkup(buttons)
            query.edit_message_text("الرجاء اختيار المستودع الذي تريد حذفه:", reply_markup=reply_markup)
        else:
            query.edit_message_text("لا توجد مستودعات متاحة حاليًا على GitHub.")

    elif query.data.startswith('heroku_app_'):
        app_name = query.data[len('heroku_app_'):]
        result = delete_heroku_app(app_name)
        if result:
            query.edit_message_text(f"تم حذف الخادم {app_name} بنجاح ✅")
        else:
            query.edit_message_text(f"فشل في حذف الخادم {app_name} ⚠️")

    elif query.data.startswith('github_repo_'):
        repo_name = query.data[len('github_repo_'):]
        result = delete_github_repository(repo_name)
        if result:
            query.edit_message_text(f"تم حذف المستودع '{repo_name}' بنجاح ✅")
        else:
            query.edit_message_text(f"فشل في حذف المستودع '{repo_name}' ⚠️")

    elif query.data == 'back':
        start(update.callback_query.message, context)

def main() -> None:
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_click))
    dp.add_handler(MessageHandler(Filters.text & Filters.private & ~Filters.command, authenticate))
    dp.add_handler(MessageHandler(Filters.document & Filters.private, create_github_repository))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
