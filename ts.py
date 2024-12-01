import os
import requests
from ssl import CERT_NONE
from gzip import decompress
from random import choice, choices
from concurrent.futures import ThreadPoolExecutor
from json import dumps
from rich import panel
from rich.columns import Columns
import pyfiglet
from rich.progress import track
import telebot
import time
from datetime import datetime
from rich.console import Console
import threading
#بزثهعههه
try:
    from websocket import create_connection
except ImportError:
    os.system("pip uninstall -y websocket websocket-client")
    os.system("pip install websocket-client rich threading datetime pyfiglet ms4")
from websocket import create_connection
Z = '\033[1;31m'  # أحمر
X = '\033[1;33m'  # أصفر
F = '\033[2;32m'  # أخضر
C = "\033[1;97m"  # أبيض
B = '\033[2;36m'  # سمائي
Y = '\033[1;34m'  # أزرق فاتح
failed = 0
success = 0
retry = 0
accounts = []
#بوثععهععع
k1 = pyfiglet.figlet_format(text=f"S1")
print("_" * 60)
print(k1)
print("_" * 60)
#مخححح
token = '6343099451:AAFTtZNt4KMds4joweF-kaIk5cQp-n-Jhyw'
if token == "":
    print("يجب إدخال ت مخحححح وكن صحيح.")
    exit()
bot = telebot.TeleBot(token)
ID = '6365543397'
os.system("clear")
print("_" * 60)
print(k1)
print("_" * 60)
time.sleep(2)
def s1(message):
    global failed, success, retry, ID, bot
    tim = datetime.now().strftime("%H : %M : %S : %f")#مضرطهههه
    username = choice("qwertyuioasdfghjklzxcvbnpm1234567890") + "".join(
        choices(list("qwertyuioasdfghjklzxcvbnpm1234567890"), k=17)
    )
    try:
        con = create_connection(
            "wss://51.79.208.190:8080/Reg",
            header=[
                "app: com.safeum.android",
                "host: None",
                "remoteIp: 51.79.208.190",
                "remotePort: 8080",
                "sessionId: None",
                "time: 2024-04-11 11:00:00",
                "url: wss://51.79.208.190:8080/Reg",
            ],
            sslopt={"cert_reqs": CERT_NONE},
        )
        con.send(dumps({"action":"Register","subaction":"Desktop","locale":"ar_IQ","gmt":"+03","password":{"m1x":"583e18fe368dce9ed5e4402fa30d655547ebdcd80a3b3375ecb0180bcc4e606f","m1y":"a123d38d02bab03aa185e5d02008a8a4f994648ea36d903545632912c8d8e7b2","m2":"27125e4f603f2cd1f862a76656ff737d4752053f4817049164f34edf85164493","iv":"e43d9f68f97937591a27ea1dda2ab2c9","message":"92ee98e3f5f81b81d9a15011d5ffd60f73757d3b6da0cff1841308d957fe88f7ca986f16530eb1323cb9f93237a328b571504afe4b80755bcdaa59c450a8a4dff5e24f8879816bcd2e48948f1e3b21a3"},"magicword":{"m1x":"fa11a01cddcf0bce44b50f39bcc468b45f7410f1b6748e1dbeb6e2fb1e4d28e9","m1y":"8ccb515502db757d18d835c78c314c389ecfac7d98c5a92b22cfe25d180c6e16","m2":"655f5a124452e01381235ae7888e0d9ef22401435dd014e58d9e8053d9cc0931","iv":"865c2d24a53cd7d91bf9d58bb4e1eeb8","message":"5b03c8000d9d34c322aa9a4bd950ffa5"},"magicwordhint":"0000","login":str(username),"devicename":"Realme RMX3269","softwareversion":"1.1.0.1640","nickname":"hfygsjctuhgfyhj","os":"AND","deviceuid":"f7a88f3e39abf27a","devicepushuid":"*cME2FmjeSj6-869LtFwnwI:APA91bGyMZ_7-tmCzlep7Fz_mWJ9AnTimC83urrBkFMXxTpZhD7Q2xBpUc4DFJIUcKzfzI9H5SqZ0_sY36rc1QJd61kprv7iHSyHtELbuPVTPBbdE75qqs6eTaCoBpmRL_i6RTZEYbFF","osversion":"and_11.0.0","id":"2142632083"}))
        response = decompress(con.recv()).decode("utf-8")
        if '"status":"Success"' in response:
            success += 1
            accounts.append(username)
            with open('users.txt', 'a') as file:
                file.write(username + "\n")
            m = f"{username}"
            bot.send_message(ID, f"<strong> <code>{m}</code> </strong>", parse_mode="html")
          
        else:
            failed += 1
    except Exception as e:
        retry += 1
start = ThreadPoolExecutor(max_workers=1000)
while True:
    start.submit(s1, None)
    print(f"""
        عدد الحسابات الناجحة ~ {success}\n
        عدد المحاولات الفاشلة ~ {failed}\n
        """)
    if success > 0:
        z = "\n".join(accounts)
        print("\n", z)
    os.system("clear")
bot.polling()#محح
