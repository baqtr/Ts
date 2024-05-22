import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters, CallbackContext

ASKING_API, MANAGING_APPS = range(2)

def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "مرحبًا! من فضلك أرسل لي Heroku API Token الخاص بك للبدء."
    )
    return ASKING_API

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

def manage_apps(update: Update, context: CallbackContext) -> int:
    api_token = context.user_data.get('api_token')
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Accept': 'application/vnd.heroku+json; version=3'
    }
    response = requests.get('https://api.heroku.com/apps', headers=headers)
    
    if response.status_code == 200:
        apps = response.json()
        num_apps = len(apps)
        
        layout = context.user_data.get('layout', 'vertical')
        
        if layout == 'vertical':
            keyboard = [[InlineKeyboardButton(app['name'], callback_data=app['id'])] for app in apps]
        elif layout == 'horizontal':
            keyboard = [[InlineKeyboardButton(app['name'], callback_data=app['id']) for app in apps]]
        else:  # mixed layout
            keyboard = []
            for i in range(0, len(apps), 2):
                row = [InlineKeyboardButton(apps[i]['name'], callback_data=apps[i]['id'])]
                if i + 1 < len(apps):
                    row.append(InlineKeyboardButton(apps[i + 1]['name'], callback_data=apps[i + 1]['id']))
                keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton(f"عدد التطبيقات: {num_apps}", callback_data='num_apps')])
        keyboard.append([InlineKeyboardButton("تبديل API", callback_data='switch_api')])
        keyboard.append([InlineKeyboardButton("تبديل ترتيب الأزرار", callback_data='switch_layout')])
        keyboard.append([InlineKeyboardButton("👨‍💻 مطور البوت", url='https://t.me/xx44g')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        if isinstance(update, Update):
            update.message.reply_text("اختر التطبيق لحذفه:", reply_markup=reply_markup)
        else:
            update.edit_message_text("اختر التطبيق لحذفه:", reply_markup=reply_markup)
        return MANAGING_APPS
    else:
        update.message.reply_text("حدث خطأ في جلب التطبيقات.")
        return ASKING_API

def button(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    
    if query.data == 'switch_api':
        query.edit_message_text(text="من فضلك أرسل لي Heroku API Token الجديد.")
        return ASKING_API
    elif query.data == 'switch_layout':
        current_layout = context.user_data.get('layout', 'vertical')
        new_layout = 'horizontal' if current_layout == 'vertical' else 'mixed' if current_layout == 'horizontal' else 'vertical'
        context.user_data['layout'] = new_layout
        return manage_apps(query, context)
    elif query.data == 'num_apps':
        return MANAGING_APPS
    elif query.data == 'back':
        return manage_apps(query, context)
    else:
        api_token = context.user_data.get('api_token')
        app_id = query.data
        headers = {
            'Authorization': f'Bearer {api_token}',
            'Accept': 'application/vnd.heroku+json; version=3'
        }
        response = requests.delete(f'https://api.heroku.com/apps/{app_id}', headers=headers)
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if response.status_code == 202:
            query.edit_message_text(text=f"تم حذف التطبيق بنجاح! (ID: {app_id})", reply_markup=reply_markup)
        else:
            query.edit_message_text(text="فشل في حذف التطبيق. حاول مرة أخرى.", reply_markup=reply_markup)

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
