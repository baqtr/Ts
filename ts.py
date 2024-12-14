import requests
import json
import telebot
import random
from telebot import types
import threading
import time

# قائمة التوكنات
API_TOKENS = [
'7550173501:AAGfQw5UOY4jNg7QfG9xhLQDgNVQp-W8c4o',
    
    '7924484400:AAFy7EXN-bBbzyElloNL7Y3uGU_E1rnuttM',
    '7882960229:AAEFemjcoX_lTBzdDMvIhMnpRCFuskVw9f4',
    '7743708826:AAFbkXBGovOa53wOt9uZZ1XNvR_RIGqL6pU',
    
    '7877154661:AAGunB3GlkfMznl8CHFq9v9325kbw3vBUC8',
   '6837495236:AAGprk4Kgt7kkz1MQ_H6OJ27Zr3gbpOx3K8',
        '6457264680:AAEJqTHvsUPE5Ztb4iwlxdyxZ2U0nz1bFZk',
    
    '7063542202:AAE-eyLE2EQHo8gIrPXXCvMCGKAUWI6p0Yc',
    
    
    '7107601491:AAE5A2rJbbsSIF8p-Vc4x3DVaECp5n8d0nY',
    '7161916020:AAHUDwiCFFx_nigu1R8zkThJMjP8VK3oTUw',
    
    '6998683016:AAE7xhxwYhvdOB-sueWRZwLudsUntzJki14',
   
    '8008365515:AAHUg86iM3A9h3YUOn-nEIh9niPAVhE3HOk',
    '7739630113:AAHpMu_NRcCmLBcuMWdKZNPzXwdJW7u-mQo',
    '7753663515:AAGqFplwOPzPuy2jbzjHIJ0hsfJ1EiUba0s',
    '8065085015:AAGhjmj8DB4mtR02JCoAo9XcQxV916K7254',
    '8138917881:AAFWE19NBNSyhtfE4joKcSKIgz72wTAM52M',

        '7796183632:AAEEqqCrsnazT7msmy_BO-xABEpwUDpnTvo',
    '7281428631:AAEFNczQspH6JFA5QwD7GJzt5FTZn1QGWq0',

        '7905581103:AAENJdpZgrWMMRV-VwXfD67m2KCeQ-q92rc',

        '7500604946:AAEiNPr5b-ANhfpVbjERDQnIQbd_PJWn-XQ',
    '7998916732:AAG_qdAx2aT1avxWsCiWHIIuXLPRJmUHnYI',
    
'8010994721:AAG-Xn-3SXsg6FgsYgotEmze9Zx9ralz1YY',

'7581614757:AAErIAqffKaPEqYv7n8IzblahAU9VDa7W_o',

'7488842737:AAHiqae7SGVjCk6Zz1G25Haq6NG0Mq-wDf0',

'8006539961:AAGxOY4X8J-OqqcULQ893ZCvcZiZqLaMiGw',

'8146796897:AAF3Y_h1tu74-4d7wuOchQg3RRZ298NSeqs',

'7051701839:AAH2QSw3tJrQnyXKG0_Xoq9UsT2A45dn9Sw',

'7955497223:AAFwFm8106CXHOCOapBfgrZRA395L-eKYiI',

'8110975976:AAHmNr-IbYYhQ7YXVWs5k7lCD0DdfCrp8Q0',
'8111288499:AAG0YXaJRaoSQu2PkidSnbIy6tTxhRs6Z3E',
'8077210784:AAEUqPNgjlneS_u3fQRCPYrtGeWMNx5f_qc',
'7445612090:AAFt2V5x0z92rWTLAGaxfnPL2FrkW9JiRMM',
'7851347903:AAF0SG7EtbRnokU70GFCFSpG5_v2jUymgeQ',
'7694758471:AAFPSHfrc_COOZ8WrxNDkaYVnEHbhwil-q0',
'7252326034:AAEXqKDcKHrAqPwILwCrE_lUriZElUeEVG0',
'7588578415:AAG-aNMEfWExP59IlvyjRdoaGOGpyTkJBrs',
'8042774423:AAEv2IZIJAg50LMAQ4y2l12TmFo88ndOO_0',
'7558794347:AAESW45SP3CTJ_TthfTP-tNoqYCPf3Dg7FI',
'7655594065:AAGUQW8rXbLmBeDQcDpqNbjORYzsuMe2AyA',
'7646829730:AAFv9-XQ2gjtELHZ1k4gjrl6_gJUUFE7-dA',
'7601318283:AAFi0YGhQUkQQvtlXoAjro3cDAnCPbVdjdI',
'7777086260:AAEL1ihCafu1bY0uchdSxQKfylbXi45UN80',
'8196639259:AAGPW9chw9spYNAVAYlrvLHzdgRmxX5tIZk',
'7920339981:AAFMwyloHRSV3P0YNT8UFnYBH-edWWwhivk',
'7881765133:AAFOyjZvcubBbSGuAiiDIFxYkRxWGxL4uJA',
'6387239251:AAEjsjok-GJxl-9mbfBCtG2rMVbt4P5qgkk',
'7689431345:AAFKJ6DibOt2miGb2H3kTyIv8qLUwFkyUTw',
'7686574892:AAHBoiEI-R_IeUWK2kitFTx1LMAuMwMLdUo'
]

# قائمة ردود الفعل
reactions = ["👍", "🌚", "😍", "🔥", "😘", "❤️‍🔥", "💋", "🙈", "❤", "❤️‍🔥", "💯"]

# دالة تفاعل البوت
def create_bot(api_token):
    bot = telebot.TeleBot(api_token)

    @bot.message_handler(commands=['start'])
    def start(message):
        name_of_C4 = f"{message.from_user.first_name}"
        text = f'''* مرحبا عزيزي * {name_of_C4} * انا بوت تفاعل برموز تعبيرية يمكنك إضافتي إلى كروب أو قناة للتفاعل*'''
        bot.send_message(message.chat.id, text, parse_mode="Markdown")

    @bot.message_handler(func=lambda message: True)
    def react_to_message(message):
        emoji = random.choice(reactions)
        attempt_react(api_token, message.chat.id, message.message_id, emoji)

    @bot.channel_post_handler(content_types=['text', 'photo', 'video', 'document'])
    def react_to_channel_post(post):
        emoji = random.choice(reactions)
        attempt_react(api_token, post.chat.id, post.message_id, emoji)

    bot.infinity_polling()

# دالة لإرسال رد الفعل مع إعادة المحاولة في حال الفشل
def attempt_react(api_token, chat_id, message_id, emoji, retries=3):
    url = f"https://api.telegram.org/bot{api_token}/setmessagereaction"
    data = {
        'chat_id': chat_id,
        'message_id': message_id,
        'reaction': json.dumps([{'type': "emoji", "emoji": emoji}])
    }
    
    for attempt in range(retries):
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print(f"Reaction sent successfully with token {api_token}")
            return response.json()
        else:
            print(f"Failed attempt {attempt + 1} for token {api_token}: {response.text}")
            time.sleep(1)  # تأخير بين المحاولات

    print(f"All attempts failed for token {api_token}")
    return None

# تشغيل جميع البوتات في وقت واحد
for token in API_TOKENS:
    threading.Thread(target=create_bot, args=(token,)).start()
