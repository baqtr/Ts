import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters, CallbackContext

# مراحل الحوار
ASKING_API, MANAGING_APPS = range(2)

# ابدأ وظيفة البوت
def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "👋 مرحبًا! من فضلك أرسل لي Heroku API Token الخاص بك للبدء."
    )
    return ASKING_API

# استقبال API والتحقق منه
def ask_api(update: Update, context: CallbackContext) -> int:
    api_token = update.message.text
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.get('https://api.heroku.com/apps', headers=headers)
    
    if response.status_code == 200:
        context.user_data['api_token'] = api_token
        update.message.reply_text("تم استقبال API بنجاح! جاري جلب التطبيقات...")
        return manage_apps(update, context)
    else:
        update.message.reply_text("API Token غير صالح. حاول مرة أخرى.")
        return ASKING_API

# جلب التطبيقات وعرضها كأزرار
def manage_apps(update: Update, context: CallbackContext) -> int:
    api_token = context.user_data.get('api_token')
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.get('https://api.heroku.com/apps', headers=headers)
    
    if response.status_code == 200:
        apps = response.json()
        keyboard = [[InlineKeyboardButton(app['name'], callback_data=app['id'])] for app in apps]
        keyboard.append([InlineKeyboardButton("تبديل API", callback_data='switch_api')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("اختر التطبيق لحذفه:", reply_markup=reply_markup)
        return MANAGING_APPS
    else:
        update.message.reply_text("حدث خطأ في جلب التطبيقات.")
        return ASKING_API

# معالجة الضغط على الأزرار
def button(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    
    if query.data == 'switch_api':
        query.edit_message_text(text="من فضلك أرسل لي Heroku API Token الجديد.")
        return ASKING_API
    else:
        api_token = context.user_data.get('api_token')
        app_id = query.data
        headers = {
            'Authorization': f'Bearer {api_token}',
            'Accept': 'application/vnd.heroku+json; version=3'
        }
        response = requests.delete(f'https://api.heroku.com/apps/{app_id}', headers=headers)
        
        if response.status_code == 202:
            query.edit_message_text(text=f"تم حذف التطبيق بنجاح! (ID: {app_id})")
            return manage_apps(update, context)
        else:
            query.edit_message_text(text="فشل في حذف التطبيق. حاول مرة أخرى.")
            return MANAGING_APPS

# إنهاء الحوار
def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('تم إنهاء الجلسة.')
    return ConversationHandler.END

def main():
    # توكن البوت الخاص بك
    TOKEN = '7046309155:AAH0f4ObaNcExF23RDQmrJJcjvkijQ4tae0'
    
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASKING_API: [MessageHandler(Filters.text & ~Filters.command, ask_api)],
            MANAGING_APPS: [CallbackQueryHandler(button)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    dp.add_handler(conv_handler)
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
