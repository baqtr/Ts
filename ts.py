import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import requests

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TELEGRAM_TOKEN = "7021020952:AAFoIRZ52WqViV7LrgtDvkLbWgCt-D8vwzk"
HEROKU_API_KEY = "HRKU-43525bf8-98dc-41db-be13-7ce5add1ee52"
GITHUB_ACCESS_TOKEN = "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"
GITHUB_USERNAME = "mwhan1"

def start(update: Update, context: CallbackContext) -> None:
    heroku_apps_count = get_heroku_apps_count()
    github_repos_count = get_github_repos_count()
    
    update.message.reply_text(
        f"أهلاً بك في بوت GitHub & VPS 🤖\n\n"
        f"عدد خوادم VPS: {heroku_apps_count}\n"
        f"عدد مستودعات GitHub: {github_repos_count}\n\n"
        "هذا البوت لتسهيل عملك للحذف كل شي التصفيه العامه احذر ان تضغط حذف الكل دون قصد للنه سيتم حذف كل شي ويعود الى الصفر ‼️‼️",
        reply_markup=get_main_keyboard()
    )

def get_main_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("عرض خوادم VPS 🚀", callback_data='heroku_apps')],
        [InlineKeyboardButton("عرض مستودعات GitHub 📚", callback_data='github_repos')],
        [InlineKeyboardButton("حذف الكل ❌", callback_data='delete_all')],
    ]
    return InlineKeyboardMarkup(keyboard)

def button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if query.data == 'heroku_apps':
        heroku_apps = get_heroku_apps()
        query.edit_message_text("خوادم VPS:\n\n{}".format(heroku_apps), reply_markup=get_main_keyboard())

    elif query.data == 'github_repos':
        github_repos = get_github_repos()
        query.edit_message_text("مستودعات GitHub:\n\n{}".format(github_repos), reply_markup=get_main_keyboard())

    elif query.data == 'delete_all':
        deleted_apps = delete_all_heroku_apps()
        deleted_repos = delete_all_github_repos()
        result_message = f"تم حذف جميع المستودعات والخوادم بنجاح.\n\nعدد المستودعات المحذوفة: {deleted_repos}\nعدد الخوام المحذوفة: {deleted_apps}"
        query.edit_message_text(result_message, reply_markup=get_main_keyboard())

    elif query.data == 'confirm_delete':
        
        pass

    elif query.data == 'cancel_delete':
        query.edit_message_text("تم الغاء الحذف.")

def get_heroku_apps_count() -> int:
    headers = {
        "Accept": "application/vnd.heroku+json; version=3",
        "Authorization": "Bearer {}".format(HEROKU_API_KEY)
    }
    response = requests.get("https://api.heroku.com/apps", headers=headers)
    if response.status_code == 200:
        return len(response.json())
    else:
        return 0

def get_github_repos_count() -> int:
    headers = {
        "Authorization": "token {}".format(GITHUB_ACCESS_TOKEN)
    }
    response = requests.get("https://api.github.com/user/repos", headers=headers)
    if response.status_code == 200:
        return len(response.json())
    else:
        return 0

def get_heroku_apps() -> str:
    apps = []
    headers = {
        "Accept": "application/vnd.heroku+json; version=3",
        "Authorization": "Bearer {}".format(HEROKU_API_KEY)
    }
    response = requests.get("https://api.heroku.com/apps", headers=headers)
    if response.status_code == 200:
        for app in response.json():
            apps.append(app['name'])
    return '\n'.join(apps)

def get_github_repos() -> str:
    repos = []
    headers = {
        "Authorization": "token {}".format(GITHUB_ACCESS_TOKEN)
    }
    response = requests.get("https://api.github.com/user/repos", headers=headers)
    if response.status_code == 200:
        for repo in response.json():
            repos.append(repo['name'])
    return '\n'.join(repos)

def delete_all_heroku_apps() -> int:
    headers = {
        "Accept": "application/vnd.heroku+json; version=3",
        "Authorization": "Bearer {}".format(HEROKU_API_KEY)
    }
    response = requests.get("https://api.heroku.com/apps", headers=headers)
    if response.status_code == 200:
        deleted_apps = 0
        for app in response.json():
            requests.delete("https://api.heroku.com/apps/{}".format(app['name']), headers=headers)
            deleted_apps += 1
        return deleted_apps
    else:
        return 0

def delete_all_github_repos() -> int:
    headers = {
        "Authorization": "token {}".format(GITHUB_ACCESS_TOKEN)
    }
    response = requests.get("https://api.github.com/user/repos", headers=headers)
    if response.status_code == 200:
        deleted_repos = 0
        for repo in response.json():
            requests.delete("https://api.github.com/repos/{}/{}".format(GITHUB_USERNAME, repo['name']), headers=headers)
            deleted_repos += 1
        return deleted_repos
    else:
        return 0

def main() -> None:
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_click))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()