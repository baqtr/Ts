import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext

# تفعيل تسجيل الأحداث
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# جلب التوكن الخاص بالبوت من متغيرات البيئة
TOKEN = os.getenv("7046309155:AAH0f4ObaNcExF23RDQmrJJcjvkijQ4tae0")
HEROKU_API_KEY = None

# دالة الترحيب
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("مرحباً بك! الرجاء إرسال مفتاح API الخاص بـ Heroku للبدء.")

# دالة لتعيين API الخاص بـ Heroku
def set_api_key(update: Update, context: CallbackContext) -> None:
    global HEROKU_API_KEY
    HEROKU_API_KEY = update.message.text.strip()
    update.message.reply_text("تم تعيين مفتاح API بنجاح. يمكنك الآن عرض التطبيقات باستخدام /apps")

# دالة للحصول على التطبيقات وعرضها كأزرار
def get_apps(update: Update, context: CallbackContext) -> None:
    if not HEROKU_API_KEY:
        update.message.reply_text("الرجاء تعيين مفتاح API باستخدام /set_api")
        return

    headers = {
        "Authorization": f"Bearer {HEROKU_API_KEY}",
        "Accept": "application/vnd.heroku+json; version=3"
    }
    response = requests.get("https://api.heroku.com/apps", headers=headers)
    
    if response.status_code == 200:
        apps = response.json()
        keyboard = [[InlineKeyboardButton(app['name'], callback_data=app['id'])] for app in apps]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("اختر تطبيق لحذفه:", reply_markup=reply_markup)
    else:
        update.message.reply_text("حدث خطأ في جلب التطبيقات. تأكد من مفتاح API.")

# دالة لحذف التطبيق
def delete_app(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    app_id = query.data
    headers = {
        "Authorization": f"Bearer {HEROKU_API_KEY}",
        "Accept": "application/vnd.heroku+json; version=3"
    }
    response = requests.delete(f"https://api.heroku.com/apps/{app_id}", headers=headers)
    
    if response.status_code == 202:
        query.edit_message_text(text=f"تم حذف التطبيق بنجاح.")
    else:
        query.edit_message_text(text=f"حدث خطأ أثناء حذف التطبيق.")

# دالة لتبديل مفتاح API
def switch_api(update: Update, context: CallbackContext) -> None:
    global HEROKU_API_KEY
    HEROKU_API_KEY = None
    update.message.reply_text("تم حذف مفتاح API الحالي. الرجاء إرسال مفتاح جديد.")

def main() -> None:
    # تأكد من أن التوكن تم جلبه بنجاح
    if not TOKEN:
        logger.error("لم يتم العثور على التوكن. تأكد من تعيين متغير البيئة TELEGRAM_BOT_TOKEN")
        return

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("set_api", set_api_key))
    dp.add_handler(CommandHandler("apps", get_apps))
    dp.add_handler(CommandHandler("switch_api", switch_api))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, set_api_key))
    dp.add_handler(CallbackQueryHandler(delete_app))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
