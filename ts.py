import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
import string
from datetime import datetime, timedelta
import psycopg2

### توكنك هنا
TOKEN = '7921859117:AAGwuT0KF1IJJMbcjYXseMxIbIhBmKjDcNM'
### id الادمن هنا
YOUR_ADMIN_ID = 6587251262

bot = telebot.TeleBot(TOKEN)

# إعداد الاتصال بقاعدة البيانات
DATABASE_URL = "postgres://u1hduks33islti:p8c8224c38062f0c82c4128d4a04532ddb7a61e9efb9dd246313941e762be76ee@ec2-3-208-156-53.compute-1.amazonaws.com:5432/d2i9fcsgc6m328"
connection = psycopg2.connect(DATABASE_URL, sslmode='require')
cursor = connection.cursor()

admin_data = {
    'products': [],
    'referral_points': 5,
    'gift_codes': {},
    'subscription_channels': {},
    'linked_channels': {}
}

def initialize_database():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            points INTEGER DEFAULT 0,
            referrals INTEGER DEFAULT 0,
            referral_code TEXT,
            used_referral BOOLEAN DEFAULT FALSE,
            gift_codes_used TEXT[]
        )
    """)
    connection.commit()

def fetch_user_data(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    return cursor.fetchone()

def insert_user_data(user_id, username, referral_code):
    cursor.execute("INSERT INTO users (user_id, username, referral_code) VALUES (%s, %s, %s)", (user_id, username, referral_code))
    connection.commit()

def update_user_points(user_id, points):
    cursor.execute("UPDATE users SET points = %s WHERE user_id = %s", (points, user_id))
    connection.commit()

def update_user_referrals(user_id, referrals):
    cursor.execute("UPDATE users SET referrals = %s WHERE user_id = %s", (referrals, user_id))
    connection.commit()

def user_exists(user_id):
    return fetch_user_data(user_id) is not None

def generate_referral_code(user_id):
    return f"REF{user_id}"

def generate_gift_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

def generate_channel_id():
    return ''.join(random.choices(string.ascii_uppercase, k=13))

def generate_product_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def register_user_if_not_exists(user_id, username):
    if not user_exists(user_id):
        referral_code = generate_referral_code(user_id)
        insert_user_data(user_id, username, referral_code)

def check_channel_subscription(user_id):
    for channel_link, channel_data in admin_data['subscription_channels'].items():
        try:
            member_status = bot.get_chat_member(channel_data['channel_id'], user_id).status
            if member_status not in ['member', 'administrator', 'creator']:
                bot.send_message(user_id, f"عزيزي عليك الاشتراك بـ قناه : {channel_link} للتمكن من استخدام البوت 🔰")
                return False
        except Exception as e:
            bot.send_message(user_id, f"خطأ في التحقق من الاشتراك: {e}")
            return False
    return True

def get_start_markup(user_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("شرح استخدام البوت 📖", callback_data="usage_guide"))
    markup.add(InlineKeyboardButton("خدمات البوت 🛒", callback_data="show_products"))
    markup.add(InlineKeyboardButton(" قناه المطور ⚙️", url="https://t.me/Mt_3z"))
    markup.add(InlineKeyboardButton("مطور البوت 💻", url="https://t.me/Mt_3u"))
    markup.add(InlineKeyboardButton("ابلاغ مشكله للمطور 🖌", callback_data="report_issue"))
    markup.add(InlineKeyboardButton("تحويل دولارات 💰", callback_data="transfer_dollars"))
    markup.add(InlineKeyboardButton("ادخال كود هديه 🎁", callback_data="enter_gift_code"),
               InlineKeyboardButton("ادخال كود احاله 💳", callback_data="enter_referral_code"))
    
    return markup

@bot.message_handler(commands=['start'])
def welcome_message(message):
    user_id = message.from_user.id
    username = message.from_user.first_name

    if not check_channel_subscription(user_id):
        return

    register_user_if_not_exists(user_id, username)

    user_info = fetch_user_data(user_id)
    bot.send_message(message.chat.id, 
                     f"اهلا بيك 👋 {username} في بوت متجر 𝓝𝓞𝓸𝓡 ⚡️\n\n"
                     "من هنا تقدر تشتري سلع كتيره مدفوعه مجانا 👌🏻\n"
                     "فقط مقابل دولارات في البوت يمكنك الحصول عليها من خلال الاحالات 🤝\n\n"
                     f"كود الاحاله الخاص بك: ` {user_info[4]} `\n"
                     f"عدد دولاراتك: {user_info[2]} ✨\n"
                     f"عدد احالاتك: {user_info[3]} ✨",
                     reply_markup=get_start_markup(user_id),
                     parse_mode='Markdown')

@bot.message_handler(commands=['adm'])
def admin_panel(message):
    if message.from_user.id == YOUR_ADMIN_ID:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("شرح اوامر الاداره 📜", callback_data="admin_commands_guide"))
        markup.add(InlineKeyboardButton("اضافه سلعه 🧺", callback_data="add_product"))
        markup.add(InlineKeyboardButton("سعر الاحاله الواحده 🗞", callback_data="set_referral_price"))
        markup.add(InlineKeyboardButton("السلع المضافة 📫", callback_data="view_products"))
        markup.add(InlineKeyboardButton("صنع كود هديه 🎁", callback_data="create_gift_code"))
        markup.add(InlineKeyboardButton("اضافه قناه اشتراك اجباري 📎", callback_data="add_subscription_channel"))
        markup.add(InlineKeyboardButton("قنوات اشتراك اجباري 🔖", callback_data="view_subscription_channels"))
        markup.add(InlineKeyboardButton("ربط قناه 📎", callback_data="link_channel"))
        markup.add(InlineKeyboardButton("القنوات المربوطه 🔒", callback_data="view_linked_channels"))
        markup.add(InlineKeyboardButton("احصائيات المستخدمين 📊", callback_data="user_statistics"))
        markup.add(InlineKeyboardButton("اضافه دولارات لمستخدم 📈", callback_data="add_dollars"))
        markup.add(InlineKeyboardButton("مسح دولارات 📉", callback_data="remove_dollars"))
        markup.add(InlineKeyboardButton("ازاعه 📣", callback_data="broadcast_message"))
        bot.send_message(message.chat.id, "اهلا بيك عزيزي المطور فـ لوحت الادمن ⚡️", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "admin_commands_guide")
def admin_commands_guide(call):
    bot.send_message(call.message.chat.id, 
                     "شرح اوامر الاداره:\n\n"
                     "<b>1. اضافا سلعه:</b> لإضافة سلعة جديدة للبوت.\n"
                     "<b>2. سعر الاحاله الواحده:</b> لتعيين سعر الإحالة.\n"
                     "<b>3. السلع المضافة:</b> لعرض السلع المضافة مسبقًا.\n"
                     "<b>4. صنع كود هديه:</b> لإنشاء كود هدية جديد.\n"
                     "<b>5. اضافا قناه اشتراك اجباري:</b> لإضافة قناة للاشتراك الإجباري.\n"
                     "<b>6. قنوات اشتراك اجباري:</b> لعرض القنوات المضافة كاشتراك إجباري.\n"
                     "<b>7. ربط قناه:</b> لربط قناة جديدة بالبوت.\n"
                     "<b>8. القنوات المربوطه:</b> لعرض القنوات المرتبطة.\n"
                     "<b>9. احصائيات المستخدمين:</b> لعرض إحصائيات حول المستخدمين.\n"
                     "<b>10. اضافا دولارات لمستخدم:</b> لإضافة دولارات لمستخدم معين.\n"
                     "<b>11. مسح دولارات:</b> لمسح دولارات من حساب مستخدم.\n"
                     "<b>12. ازاعه:</b> لإرسال رسالة جماعية لكل المستخدمين.",
                     parse_mode='HTML') 

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    username = call.from_user.first_name

    if not check_channel_subscription(user_id):
        return

    register_user_if_not_exists(user_id, username)

    if call.data == "show_products":
        show_products(call.message, 0) 
    elif call.data == "add_product":
        bot.send_message(call.message.chat.id, "ادخل اسم السلعة:")
        bot.register_next_step_handler(call.message, process_product_name)
    elif call.data == "set_referral_price":
        bot.send_message(call.message.chat.id, "اكتب سعر الاحاله الواحده:")
        bot.register_next_step_handler(call.message, process_referral_price)
    elif call.data == "view_products":
        view_admin_products(call.message, 0) 
    elif call.data.startswith("product_"):
        product_detail(call)
    elif call.data.startswith("buy_"):
        buy_product(call)
    elif call.data.startswith("delete_"):
        delete_product(call)
    elif call.data == "enter_referral_code":
        enter_referral_code(call.message)
    elif call.data == "enter_gift_code":
        enter_gift_code(call.message)
    elif call.data == "create_gift_code":
        create_gift_code(call.message)
    elif call.data == "add_subscription_channel":
        add_subscription_channel(call.message)
    elif call.data == "view_subscription_channels":
        view_subscription_channels(call.message)
    elif call.data == "link_channel":
        link_channel(call.message)
    elif call.data == "view_linked_channels":
        view_linked_channels(call.message)
    elif call.data == "transfer_dollars":
        start_dollars_transfer(call.message)
    elif call.data == "user_statistics":
        user_statistics(call.message)
    elif call.data == "add_dollars":
        add_dollars_to_user(call.message)
    elif call.data == "remove_dollars":
        remove_dollars_from_user(call.message)
    elif call.data == "report_issue":
        bot.send_message(call.message.chat.id, "اكتب رسالتك وسيتم ارسالها لمطور البوت:")
        bot.register_next_step_handler(call.message, process_report_issue)
    elif call.data == "broadcast_message":
        bot.send_message(call.message.chat.id, "اكتب رسالتك وسيتم ارسالها لكل مستخدمين البوت:")
        bot.register_next_step_handler(call.message, process_broadcast_message)
    elif call.data == "usage_guide":
        bot.send_message(call.message.chat.id, 
                         "شرح استخدام البوت:\n\n"
                         "1. يمكنك استخدام الأزرار المتاحة في القائمة للوصول إلى مختلف خدمات البوت.\n"
                         "2. لتحويل الدولارات، اضغط على زر 'تحويل دولارات 💰'.\n"
                         "3. لاستخدام كود هدية، اضغط على زر 'ادخال كود هديه 🎁'.\n"
                         "4. للإبلاغ عن أي مشكلة، استخدم زر 'ابلاغ مشكله للمطور 🖌'.\n"
                         "5. إذا كنت بحاجة لمزيد من المساعدة، تواصل مع مطور البوت عبر زر 'مطور البوت ⚙️'.")

def process_report_issue(message):
    user_id = message.from_user.id
    report_message = message.text.strip()
    developer_id = YOUR_ADMIN_ID 

    bot.send_message(developer_id, 
                     f"🗳 تم الابلاغ عن مشكله من {user_id}:\n{report_message}")
    bot.send_message(message.chat.id, "تم ارسالها للمطور.")

def process_broadcast_message(message):
    broadcast_text = message.text.strip()
    cursor.execute("SELECT user_id FROM users")
    user_ids = cursor.fetchall()
    total_users = len(user_ids)
    failed_users = []

    for user_id in user_ids:
        try:
            bot.send_message(user_id[0], broadcast_text)
        except Exception:
            failed_users.append(user_id[0])

    success_count = total_users - len(failed_users)
    bot.send_message(message.chat.id, 
                     f"تم ارسال الرساله بنجاح\n"
                     f"ارسلت لـ {success_count} مستخدمين\n"
                     f"فشل ارسالها لـ {len(failed_users)} مستخدمين")

def process_referral_price(message):
    try:
        referral_price = int(message.text)
        admin_data['referral_points'] = referral_price
        bot.send_message(message.chat.id, f"تم تعيين سعر الإحالة إلى {referral_price} دولار.")
    except ValueError:
        bot.send_message(message.chat.id, "برجاء إدخال رقم صحيح للسعر.")

def show_products(message, page):
    products_per_page = 8
    start_index = page * products_per_page
    end_index = start_index + products_per_page
    products_to_show = admin_data['products'][start_index:end_index]

    if not products_to_show:
        bot.send_message(message.chat.id, "لا توجد سلع متاحة حالياً.")
        return

    markup = InlineKeyboardMarkup()
    for product in products_to_show:
        markup.add(InlineKeyboardButton(f"{product['name']} | {product['points']} دولار", callback_data=f"product_{product['id']}"))
    
    if page > 0: 
        markup.add(InlineKeyboardButton("السابق ⏪", callback_data=f"previous_page_{page - 1}"))
    if end_index < len(admin_data['products']):  
        markup.add(InlineKeyboardButton("التالي ⏩", callback_data=f"next_page_{page + 1}"))

    bot.send_message(message.chat.id, f"السلع المعروضة:\n\nصفحة {page + 1} من {((len(admin_data['products']) - 1) // products_per_page) + 1}", reply_markup=markup)

def view_admin_products(message, page):
    products_per_page = 8
    start_index = page * products_per_page
    end_index = start_index + products_per_page
    products_to_show = admin_data['products'][start_index:end_index]

    if not products_to_show:
        bot.send_message(message.chat.id, "لا توجد سلع مضافة حالياً.")
        return

    markup = InlineKeyboardMarkup()
    for product in products_to_show:
        markup.add(InlineKeyboardButton(f"{product['name']} | {product['points']} دولار", callback_data=f"product_{product['id']}"))
    
    if page > 0: 
        markup.add(InlineKeyboardButton("السابق ⏪", callback_data=f"previous_page_{page - 1}"))
    if end_index < len(admin_data['products']): 
        markup.add(InlineKeyboardButton("التالي ⏩", callback_data=f"next_page_{page + 1}"))

    bot.send_message(message.chat.id, f"السلع المضافة:\n\nصفحة {page + 1} من {((len(admin_data['products']) - 1) // products_per_page) + 1}", reply_markup=markup)

def process_product_name(message):
    product_name = message.text
    bot.send_message(message.chat.id, "ارسل السلعة (صورة، ملف، أو نص):")
    bot.register_next_step_handler(message, process_product_content, product_name)

def process_product_content(message, product_name):
    product_content = None
    file_id = None
    content_type = message.content_type

    if content_type == 'text':
        product_content = message.text
    elif content_type == 'photo':
        file_id = message.photo[-1].file_id
    elif content_type == 'document':
        file_id = message.document.file_id
    else:
        bot.send_message(message.chat.id, "الرجاء ارسال صورة أو ملف أو نص.")
        return

    bot.send_message(message.chat.id, "ادخل وصف السلعة:")
    bot.register_next_step_handler(message, process_product_description, product_name, product_content, file_id, content_type)

def process_product_description(message, product_name, product_content, file_id, content_type):
    product_description = message.text
    bot.send_message(message.chat.id, "ادخل سعر السلعة بالدولارات:")
    bot.register_next_step_handler(message, process_product_price, product_name, product_content, file_id, product_description, content_type)

def process_product_price(message, product_name, product_content, file_id, product_description, content_type):
    try:
        product_price = int(message.text)
        product_id = len(admin_data['products']) + 1
        product_identifier = generate_product_id() 
        admin_data['products'].append({
            'id': product_id,
            'name': product_name,
            'content': product_content,
            'file_id': file_id,
            'description': product_description,
            'points': product_price,
            'content_type': content_type,
            'identifier': product_identifier 
        })
        bot.send_message(message.chat.id, f"تم إضافة السلعة {product_name} بنجاح بسعر {product_price} دولار!\nمعرف السلعة: {product_identifier}")
        
        notify_linked_channels(
            f"تم اضافه سلعه جديده للبوت ✅\n"
            f"اسم السلعه : {product_name} ✨\n"
            f"وصف السلعه : {product_description}\n"
            f"سعرها : {product_price} دولار 🔸\n"
            f"✔️"
        )
    except ValueError:
        bot.send_message(message.chat.id, "برجاء إدخال رقم صحيح للسعر.")

def product_detail(call):
    if not check_channel_subscription(call.from_user.id):
        return

    product_id = int(call.data.split("_")[1])
    product = next((p for p in admin_data['products'] if p['id'] == product_id), None)

    if product:
        markup = InlineKeyboardMarkup()
        if call.from_user.id == YOUR_ADMIN_ID:
            markup.add(InlineKeyboardButton("حذف", callback_data=f"delete_{product_id}"))
        markup.add(InlineKeyboardButton("شراء", callback_data=f"buy_{product_id}"))

        if product['content_type'] == 'text':
            message_text = (
                f"وصف السلعة:\n{product['description']}\n\nاختر ما تريد:"
            )
            bot.send_message(call.message.chat.id, message_text, reply_markup=markup)
        elif product['content_type'] == 'photo':
            bot.send_photo(call.message.chat.id, product['file_id'], caption=f"وصف السلعة:\n{product['description']}\n\nاختر ما تريد:", reply_markup=markup)
        elif product['content_type'] == 'document':
            bot.send_document(call.message.chat.id, product['file_id'], caption=f"وصف السلعة:\n{product['description']}\n\nاختر ما تريد:", reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, "السلعة غير موجودة.")

def delete_product(call):
    if not check_channel_subscription(call.from_user.id):
        return

    product_id = int(call.data.split("_")[1])
    
    product_index = next((index for index, p in enumerate(admin_data['products']) if p['id'] == product_id), None)

    if product_index is not None:
        deleted_product = admin_data['products'].pop(product_index)
        bot.send_message(call.message.chat.id, f"تم حذف السلعة بنجاح.\nمعرف السلعة المحذوف: {deleted_product['identifier']}")
    else:
        bot.send_message(call.message.chat.id, "فشل الحذف، السلعة غير موجودة.")

def buy_product(call):
    if not check_channel_subscription(call.from_user.id):
        return

    user_id = call.from_user.id
    product_id = int(call.data.split("_")[1])
    product = next((p for p in admin_data['products'] if p['id'] == product_id), None)

    if product:
        user_info = fetch_user_data(user_id)
        user_dollars = user_info[2]
        if user_dollars >= product['points']:
            update_user_points(user_id, user_dollars - product['points'])

            if product['content_type'] == 'text':
                message_text = (
                    f"تم شراء السلعة بنجاح: {product['name']}!\n"
                    f"السلعة:\n{product['content']}\n"  
                    f"وصف:\n{product['description']}" 
                )
                bot.send_message(call.message.chat.id, message_text)
            elif product['content_type'] == 'photo':
                bot.send_photo(call.message.chat.id, product['file_id'], caption=f"اسم السلعة: {product['name']}\nوصف السلعة:\n{product['description']}")
            elif product['content_type'] == 'document':
                bot.send_document(call.message.chat.id, product['file_id'], caption=f"اسم السلعة: {product['name']}\nوصف السلعة:\n{product['description']}")

            notify_linked_channels(
                f"تم اتمام عمليه الشراء من المستخدم : {user_id} ✅\n"
                f"السلعه : {product['name']} 📚\n"
                f"عدد دولاراته الحالي : {user_info[2] - product['points']} 🔸\n"
                f"عدد دولارات السلعه : {product['points']} 🔸"
            )
        else:
            bot.send_message(call.message.chat.id, 
                             f"عذراً، دولاراتك غير كافية. لديك: {user_dollars} دولار و سعر السلعة: {product['points']} دولار.\n"
                             f"لتجميع دولارات استعمل رمز الاحاله الخاص بك: {user_info[4]}")
    else:
        bot.send_message(call.message.chat.id, "السلعة غير موجودة.")

def enter_referral_code(message):
    user_id = message.from_user.id
    username = message.from_user.first_name

    if not check_channel_subscription(user_id):
        return

    register_user_if_not_exists(user_id, username)

    user_info = fetch_user_data(user_id)
    if user_info[5]:
        bot.send_message(message.chat.id, "الحد الاقصي للحساب الواحد في ادخال كود الاحاله هوا 1 لم تصل الاحاله ❌")
        return
    
    bot.send_message(message.chat.id, "اكتب كود الاحاله:")
    bot.register_next_step_handler(message, process_referral_code)

def process_referral_code(message):
    user_id = message.from_user.id
    referral_code = message.text.strip()

    if not check_channel_subscription(user_id):
        return

    user_info = fetch_user_data(user_id)
    if user_info[5]:
        bot.send_message(message.chat.id, "الحد الاقصي للحساب الواحد في ادخال كود الاحاله هوا 1 لم تصل الاحاله ❌")
        return

    cursor.execute("SELECT * FROM users WHERE referral_code = %s AND user_id != %s", (referral_code, user_id))
    referral_user = cursor.fetchone()

    if referral_user:
        update_user_points(referral_user[0], referral_user[2] + admin_data['referral_points'])
        update_user_referrals(referral_user[0], referral_user[3] + 1)
        cursor.execute("UPDATE users SET used_referral = TRUE WHERE user_id = %s", (user_id,))
        connection.commit()

        bot.send_message(referral_user[0], 
                         f"🔸تم تسجيل ({user_id}) | دولارات مكتسبه {admin_data['referral_points']} عدد دولاراتك الكلي {referral_user[2] + admin_data['referral_points']}🔸")
        bot.send_message(message.chat.id, "تم تسجيل الاحاله بنجاح")
        return

    bot.send_message(message.chat.id, "الكود خطأ او انت سجلت بـ كود من قبل ❌")

def create_gift_code(message):
    if not check_channel_subscription(message.from_user.id):
        return

    bot.send_message(message.chat.id, "ادخل عدد الدولارات في كود الهدية:")
    bot.register_next_step_handler(message, process_gift_points)

def process_gift_points(message):
    try:
        points = int(message.text)
        bot.send_message(message.chat.id, "ادخل عدد الأشخاص الذين يمكنهم الحصول على الهدية:")
        bot.register_next_step_handler(message, process_gift_people_count, points)
    except ValueError:
        bot.send_message(message.chat.id, "برجاء إدخال رقم صحيح للدولارات.")

def process_gift_people_count(message, points):
    try:
        people_count = int(message.text)
        bot.send_message(message.chat.id, "ادخل مدة الكود (مثل d 1):")
        bot.register_next_step_handler(message, process_gift_duration, points, people_count)
    except ValueError:
        bot.send_message(message.chat.id, "برجاء إدخال رقم صحيح لعدد الأشخاص.")

def process_gift_duration(message, points, people_count):
    try:
        duration = message.text.strip().split()
        time_unit = duration[0]
        time_value = int(duration[1])

        if time_unit not in ['m', 'h', 'd', 'mm', 'yy']:
            raise ValueError("وحدة زمنية غير صحيحة.")

        if time_unit == 'm':
            expiry_date = datetime.now() + timedelta(minutes=time_value)
        elif time_unit == 'h':
            expiry_date = datetime.now() + timedelta(hours=time_value)
        elif time_unit == 'd':
            expiry_date = datetime.now() + timedelta(days=time_value)
        elif time_unit == 'mm':
            expiry_date = datetime.now() + timedelta(days=30 * time_value)
        elif time_unit == 'yy':
            expiry_date = datetime.now() + timedelta(days=365 * time_value)

        gift_code = generate_gift_code()
        admin_data['gift_codes'][gift_code] = {
            'points': points,
            'people_count': people_count,
            'expiry_date': expiry_date,
            'used_by': set()
        }

        bot.send_message(message.chat.id,
                         f"تم صنع كود هدية جديد 🎉\n"
                         f"الكود: `{gift_code}` 🎁\n"  
                         f"متاح لـ {people_count} شخص\n"
                         f"تاريخ الانتهاء: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')} 📆\n"
                         f"✔️",
                         parse_mode='Markdown') 
        
        notify_linked_channels(
            f"تم صنع كود هدية جديد 🎉\n"
            f"الكود: `{gift_code}` 🎁\n" 
            f"متاح لـ {people_count} شخص\n"
            f"تاريخ الانتهاء: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')} 📆\n"
            f"✔️"
        )  
    
    except (ValueError, IndexError):
        bot.send_message(message.chat.id, "صيغة غير صحيحة للمدة. استخدم صيغة مثل d 1.")

def enter_gift_code(message):
    if not check_channel_subscription(message.from_user.id):
        return

    bot.send_message(message.chat.id, "ادخل كود الهدية:")
    bot.register_next_step_handler(message, process_gift_code)

def process_gift_code(message):
    user_id = message.from_user.id
    gift_code = message.text.strip()

    if not check_channel_subscription(user_id):
        return

    if gift_code not in admin_data['gift_codes']:
        bot.send_message(message.chat.id, "الكود غير صحيح.")
        return

    code_data = admin_data['gift_codes'][gift_code]

    if user_id in code_data['used_by']:
        bot.send_message(message.chat.id, "قد حصلت على هذه الهدية من قبل.")
        return

    if len(code_data['used_by']) >= code_data['people_count']:
        bot.send_message(message.chat.id, "عدد المستخدمين لهذا الكود مكتمل.")
        return

    if datetime.now() > code_data['expiry_date']:
        bot.send_message(message.chat.id, "الكود منتهي الصلاحية.")
        return

    code_data['used_by'].add(user_id)

    previous_dollars = fetch_user_data(user_id)[2]
    update_user_points(user_id, previous_dollars + code_data['points'])
    current_dollars = fetch_user_data(user_id)[2]

    bot.send_message(message.chat.id,
                     f"تم الحصول على الهدية 🎁\n"
                     f"دولاراتك قبل: {previous_dollars}\n"
                     f"دولاراتك بعد: {current_dollars}")

def add_subscription_channel(message):
    if not check_channel_subscription(message.from_user.id):
        return

    bot.send_message(message.chat.id, "ادخل رابط القناة لإضافتها كاشتراك إجباري:")
    bot.register_next_step_handler(message, process_subscription_channel)

def process_subscription_channel(message):
    channel_link = message.text.strip()

    try:
        channel_id = bot.get_chat(channel_link).id
        channel_identifier = generate_channel_id()
        admin_data['subscription_channels'][channel_link] = {'channel_id': channel_id, 'identifier': channel_identifier}
        bot.send_message(message.chat.id, "تم إضافة اشتراك إجباري بنجاح.")
    except Exception as e:
        bot.send_message(message.chat.id, f"حدث خطأ في إضافة القناة: {e}")

def view_subscription_channels(message):
    if not check_channel_subscription(message.from_user.id):
        return

    if not admin_data['subscription_channels']:
        bot.send_message(message.chat.id, "لا توجد قنوات اشتراك إجباري حالياً.")
        return

    channels_info = "قنواتك اشتراك إجباري:\n\n"
    for link, data in admin_data['subscription_channels'].items():
        channels_info += f"{link} : معرف القناة : {data['identifier']}\n"

    bot.send_message(message.chat.id, channels_info)

def link_channel(message):
    if not check_channel_subscription(message.from_user.id):
        return

    bot.send_message(message.chat.id, "ادخل معرف القناة لربطها بالبوت:")
    bot.register_next_step_handler(message, process_link_channel)

def process_link_channel(message):
    channel_username = message.text.strip()

    try:
        chat = bot.get_chat(channel_username)
        if chat.type != "channel":
            bot.send_message(message.chat.id, "هذا المعرف ليس لقناة.")
            return

        channel_id = chat.id
        channel_identifier = generate_channel_id()
        admin_data['linked_channels'][channel_username] = {'channel_id': channel_id, 'identifier': channel_identifier}
        bot.send_message(message.chat.id, "تم الربط بنجاح. تأكد من أن البوت أدمن في القناة.")
    except Exception as e:
        bot.send_message(message.chat.id, f"حدث خطأ في ربط القناة: {e}")

def view_linked_channels(message):
    if not check_channel_subscription(message.from_user.id):
        return

    if not admin_data['linked_channels']:
        bot.send_message(message.chat.id, "لا توجد قنوات مربوطة حالياً.")
        return

    channels_info = "القنوات المربوطة:\n\n"
    for username, data in admin_data['linked_channels'].items():
        channels_info += f"{username} : معرف القناة : {data['identifier']}\n"

    bot.send_message(message.chat.id, channels_info)

def notify_linked_channels(message_text):
    for channel_data in admin_data['linked_channels'].values():
        try:
            bot.send_message(channel_data['channel_id'], message_text)
        except Exception as e:
            print(f"خطأ في إرسال الرسالة إلى القناة {channel_data['channel_id']}: {e}")

@bot.message_handler(commands=['del'])
def delete_subscription_channel(message):
    try:
        channel_identifier = message.text.split()[1].strip()
        channel_link_to_delete = None

        for link, data in admin_data['subscription_channels'].items():
            if data['identifier'] == channel_identifier:
                channel_link_to_delete = link
                break

        if channel_link_to_delete:
            del admin_data['subscription_channels'][channel_link_to_delete]
            bot.send_message(message.chat.id, "تم مسح القناة بنجاح.")
        else:
            bot.send_message(message.chat.id, "لم يتم العثور على القناة بالمعرف المدخل.")
    except IndexError:
        bot.send_message(message.chat.id, "يرجى إدخال الأمر بالشكل الصحيح: /del <معرف القناة>")

@bot.message_handler(commands=['delr'])
def delete_linked_channel(message):
    try:
        channel_identifier = message.text.split()[1].strip()
        channel_link_to_delete = None

        for username, data in admin_data['linked_channels'].items():
            if data['identifier'] == channel_identifier:
                channel_link_to_delete = username
                break

        if channel_link_to_delete:
            del admin_data['linked_channels'][channel_link_to_delete]
            bot.send_message(message.chat.id, "تم مسح قناة الربط بنجاح.")
        else:
            bot.send_message(message.chat.id, "لم يتم العثور على القناة بالمعرف المدخل.")
    except IndexError:
        bot.send_message(message.chat.id, "يرجى إدخال الأمر بالشكل الصحيح: /delr <معرف القناة>")

def start_dollars_transfer(message):
    if not check_channel_subscription(message.from_user.id):
        return

    bot.send_message(message.chat.id, "ادخل ID الشخص لتحويل دولارات اليه:")
    bot.register_next_step_handler(message, process_transfer_id)

def process_transfer_id(message):
    try:
        target_user_id = int(message.text.strip())
        if not user_exists(target_user_id):
            bot.send_message(message.chat.id, "المعرف غير موجود في قاعدة البيانات.")
        else:
            bot.send_message(message.chat.id, "اكتب عدد دولارات المراد تحويلها للمستخدم | لالغاء العمليه اضغط /st")
            bot.register_next_step_handler(message, process_transfer_amount, target_user_id)
    except ValueError:
        bot.send_message(message.chat.id, "يرجى إدخال معرف صالح.")

def process_transfer_amount(message, target_user_id):
    if message.text.strip() == "/st":
        bot.send_message(message.chat.id, "تم ايقاف العمليه.")
        return

    try:
        transfer_amount = int(message.text.strip())
        sender_user_id = message.from_user.id

        if transfer_amount <= 0:
            bot.send_message(message.chat.id, "يرجى إدخال مبلغ صحيح.")
            return

        user_info = fetch_user_data(sender_user_id)
        if user_info[2] < transfer_amount:
            bot.send_message(message.chat.id, "عزيزي دولاراتك غير كافيه 🔸\nلا يمكنك تحويل دولارات.")
            return

        update_user_points(sender_user_id, user_info[2] - transfer_amount)
        update_user_points(target_user_id, fetch_user_data(target_user_id)[2] + transfer_amount)

        bot.send_message(message.chat.id,
                         f"تم اكتمال عمليه التحويل بنجاح ✅\n"
                         f"المحول اليه : {target_user_id} ✨\n"
                         f"المبلغ المحول : {transfer_amount} 🔸\n"
                         f"عدد دولاراتك الحالي : {user_info[2] - transfer_amount} 🔸\n"
                         f"✔️")

        bot.send_message(target_user_id,
                         f"تم تحويل مبلغ {transfer_amount} ✅\n"
                         f"الشخص المحول : {sender_user_id} ✨\n"
                         f"عدد دولاراتك الكلي : {fetch_user_data(target_user_id)[2]} 🔸\n"
                         f"✔️")
    except ValueError:
        bot.send_message(message.chat.id, "يرجى إدخال مبلغ صحيح.")

def user_statistics(message):
    if not check_channel_subscription(message.from_user.id):
        return

    statistics = "إحصائيات المستخدمين:\n\n"
    cursor.execute("SELECT user_id, points FROM users")
    users_data = cursor.fetchall()
    total_users = len(users_data)
    for user_id, points in users_data:
        statistics += f"{user_id} | {points}\n"

    statistics += f"\nعدد المستخدمين الكلي للبوت: {total_users}"

    bot.send_message(message.chat.id, statistics)

def add_dollars_to_user(message):
    if not check_channel_subscription(message.from_user.id):
        return

    bot.send_message(message.chat.id, "اكتب معرف المستخدم")
 
def add_dollars_to_user(message):
    if not check_channel_subscription(message.from_user.id):
        return

    bot.send_message(message.chat.id, "اكتب معرف المستخدم أو كود الإحالة الخاص به:")
    bot.register_next_step_handler(message, process_add_dollars_user)

def process_add_dollars_user(message):
    user_identifier = message.text.strip()
    target_user_id = None

    cursor.execute("SELECT user_id FROM users WHERE user_id = %s OR referral_code = %s", (user_identifier, user_identifier))
    user_data = cursor.fetchone()

    if user_data:
        target_user_id = user_data[0]
        bot.send_message(message.chat.id, "ادخل عدد الدولارات المراد إرسالها:")
        bot.register_next_step_handler(message, process_add_dollars_amount, target_user_id)
    else:
        bot.send_message(message.chat.id, "المستخدم غير موجود.")

def process_add_dollars_amount(message, target_user_id):
    try:
        dollars_to_add = int(message.text.strip())
        if dollars_to_add <= 0:
            bot.send_message(message.chat.id, "برجاء إدخال عدد دولارات صحيح.")
            return

        previous_dollars = fetch_user_data(target_user_id)[2]
        update_user_points(target_user_id, previous_dollars + dollars_to_add)
        current_dollars = fetch_user_data(target_user_id)[2]

        bot.send_message(message.chat.id,
                         f"تم إرسال الدولارات للمستخدم ✅\n"
                         f"دولاراته قبل: {previous_dollars} 🔸\n"
                         f"دولاراته بعد: {current_dollars} 🔸\n"
                         f"✔️")

        bot.send_message(target_user_id,
                         f"قام مالك البوت بإرسال إليك دولارات ✅\n"
                         f"عدد الدولارات المرسلة: {dollars_to_add} 🔸\n"
                         f"عدد دولاراتك الكلي: {current_dollars} 🔸\n"
                         f"✔️")
    except ValueError:
        bot.send_message(message.chat.id, "برجاء إدخال عدد دولارات صحيح.")

def remove_dollars_from_user(message):
    if not check_channel_subscription(message.from_user.id):
        return

    bot.send_message(message.chat.id, "اكتب معرف المستخدم أو كود الإحالة الخاص به:")
    bot.register_next_step_handler(message, process_remove_dollars_user)

def process_remove_dollars_user(message):
    user_identifier = message.text.strip()
    target_user_id = None

    cursor.execute("SELECT user_id FROM users WHERE user_id = %s OR referral_code = %s", (user_identifier, user_identifier))
    user_data = cursor.fetchone()

    if user_data:
        target_user_id = user_data[0]
        user_dollars = fetch_user_data(target_user_id)[2]
        bot.send_message(message.chat.id,
                         f"دولارات المستخدم: {user_dollars}\n"
                         "اكتب عدد دولارات لمسحه | لإلغاء العملية اكتب /str")
        bot.register_next_step_handler(message, process_remove_dollars_amount, target_user_id)
    else:
        bot.send_message(message.chat.id, "المستخدم غير موجود.")

def process_remove_dollars_amount(message, target_user_id):
    if message.text.strip() == "/str":
        bot.send_message(message.chat.id, "تم إيقاف العملية ✅")
        return

    try:
        dollars_to_remove = int(message.text.strip())
        if dollars_to_remove <= 0:
            bot.send_message(message.chat.id, "برجاء إدخال عدد دولارات صحيح.")
            return

        user_dollars = fetch_user_data(target_user_id)[2]

        if user_dollars < dollars_to_remove:
            bot.send_message(message.chat.id, 
                             f"لا يمكنك مسح {dollars_to_remove} دولار من {user_dollars} دولار\n"
                             f"يمكنك مسح {user_dollars}")
            return

        update_user_points(target_user_id, user_dollars - dollars_to_remove)
        current_dollars = fetch_user_data(target_user_id)[2]

        bot.send_message(message.chat.id, 
                         f"تم مسح دولارات مستخدم ✅\n"
                         f"عدد الدولارات الممسوحة: {dollars_to_remove} 🔸\n"
                         f"عدد دولاراته الحالي: {current_dollars} 🔸\n"
                         f"✔️")

        bot.send_message(target_user_id,
                         f"قام المالك بحذف دولارات منك 🔹\n"
                         f"عدد الدولارات الممسوحة: {dollars_to_remove} 🔸\n"
                         f"عدد دولاراتك الحالي: {current_dollars} 🔸\n"
                         f"🔴")
    except ValueError:
        bot.send_message(message.chat.id, "برجاء إدخال عدد دولارات صحيح.")

initialize_database()
bot.infinity_polling()
