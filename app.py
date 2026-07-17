import os
import re
import sys
import time
import json
import random
import logging
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

import requests
import telebot
from telebot import types
from flask import Flask, request
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ==================== التكوين الأساسي للبوت ====================
BOT_TOKEN = "8320518146:AAHNSvwvKgjH_G_YHadfPHgXqz60QrALq9s"
ADMIN_ID = 7242923713
PROOF_CHAT_ID = -1004477473385
MAINTENANCE_MODE = False
MAINTENANCE_MESSAGE = "⚠️ البوت حاليا في وضع الصيانة، حاول لاحقا."

# إعداد معالج أخطاء مخصص لطباعة أي مشكلة بوضوح في سجلات Render
class BotExceptionHandler(telebot.ExceptionHandler):
    def handle(self, exception):
        logging.error(f"❌ خطأ داخلي في البوت: {exception}", exc_info=True)
        return True

# ⚡ الحل السحري: تعطيل التخييط (threaded=False) ليعمل البوت بشكل متزامن مع Gunicorn ⚡
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=False, exception_handler=BotExceptionHandler())

# إعداد سيرفر Flask لـ Render
app = Flask(__name__)

# جلب رابط الويب الخاص بك تلقائياً، مع وضع رابطك الفعلي كاحتياطي مضمون
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://djezzy-xpqu.onrender.com")

# ==================== إعداد الويب هوك (Webhook) ====================
@app.route('/')
def home():
    try:
        # نقوم بمسح الويب هوك القديم أولاً ثم إعادة تعيينه لضمان التحديث التام
        bot.remove_webhook()
        time.sleep(0.1)
        bot.set_webhook(url=f"{RENDER_URL}/{BOT_TOKEN}")
        return "🚀 Djezzy Telegram Bot is Live & Running on Render using Webhooks!", 200
    except Exception as e:
        return f"⚠️ Bot is running, but Webhook failed to set: {e}", 500

@app.route('/' + BOT_TOKEN, methods=['POST'])
def get_telegram_message():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    else:
        return "Forbidden", 403

# ==================== إعدادات جيزي والملفات ====================
USE_PROXY = False
PROXIES = None

OFFER_CODES = {
    'offer_1': "GIFTWALKWIN2GO",
    'offer_2': "BTLINTSPEEDDAY2Go",
    'offer_3': "BTL500MBDAY",
    'offer_4': "BTLINTSPEED300DA10GO",
    'offer_5': "BTLINTSPEED1000DA30GO",
    'offer_6': "BTLINTSPEED1500DA60GO",
    'offer_7': "BTLHYBMONTHLY800DA",
    'offer_8': "BTLHYBMONTHLY1000DA",
    'offer_9': "BTL2C2000"
}

ALL_OFFERS = {
    'offer_1': {'offer_id': "offer_1", 'name': "🎁 2GB مجاناً", 'code': OFFER_CODES['offer_1'], 'amount': "2GB", 'type': "free", 'price': "مجاني", 'duration': "24 ساعة"},
    'offer_2': {'offer_id': "offer_2", 'name': "⚡ 4GB (70 DA)", 'code': OFFER_CODES['offer_2'], 'amount': "4GB", 'type': "paid", 'price': "70 DA", 'duration': "24 ساعة"},
    'offer_3': {'offer_id': "offer_3", 'name': "🤝 5GB (90 DA)", 'code': OFFER_CODES['offer_3'], 'amount': "5GB", 'type': "paid", 'price': "90 DA", 'duration': "24 ساعة"},
    'offer_4': {'offer_id': "offer_4", 'name': "🚀 10GB (300 DA)", 'code': OFFER_CODES['offer_4'], 'amount': "10GB", 'type': "paid", 'price': "300 DA", 'duration': "3 أيام"},
    'offer_5': {'offer_id': "offer_5", 'name': "💎 30GB (1000 DA)", 'code': OFFER_CODES['offer_5'], 'amount': "30GB", 'type': "paid", 'price': "1000 DA", 'duration': "30 يوم"},
    'offer_6': {'offer_id': "offer_6", 'name': "👑 60GB (1500 DA)", 'code': OFFER_CODES['offer_6'], 'amount': "60GB", 'type': "paid", 'price': "1500 DA", 'duration': "30 يوم"},
    'offer_7': {'offer_id': "offer_7", 'name': "👑 IMTIYAZ 800DA", 'code': OFFER_CODES['offer_7'], 'amount': "15GB + 2000DA", 'type': "paid", 'price': "800 DA", 'duration': "30 يوم"},
    'offer_8': {'offer_id': "offer_8", 'name': "👑 IMTIYAZ 1000DA", 'code': OFFER_CODES['offer_8'], 'amount': "20GB + 3000DA", 'type': "paid", 'price': "1000 DA", 'duration': "30 يوم"},
    'offer_9': {'offer_id': "offer_9", 'name': "👑 IMTIYAZ 2000DA", 'code': OFFER_CODES['offer_9'], 'amount': "70GB", 'type': "paid", 'price': "2000 DA", 'duration': "30 يوم"}
}

HEADERS = {
    'User-Agent': "MobileApp/3.0.0",
    'Accept': "application/json",
    'Content-Type': "application/json",
    'accept-language': "fr",
    'Connection': "keep-alive"
}

CLIENT_ID = "87pIExRhxBb3_wGsA5eSEfyATloa"
CLIENT_SECRET = "uf82p68Bgisp8Yg1Uz8Pf6_v1XYa"
BASE_URL = "https://apim.djezzy.dz/mobile-api"

REGISTERED_NUMBERS_FILE = "registered_numbers.json"
REGISTERED_USERS_FILE = "registered_users.json"
CHANNELS_FILE = "channels.json"
USER_DATA_FILE = "user_db.json"

# تهيئة وتأمين الملفات المحلية
for filename in [REGISTERED_NUMBERS_FILE, REGISTERED_USERS_FILE, CHANNELS_FILE, USER_DATA_FILE]:
    if not os.path.exists(filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({} if filename == USER_DATA_FILE else [], f, ensure_ascii=False, indent=2)

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.FileHandler('djezzy_bot.log'), logging.StreamHandler(sys.stdout)]
)

session = requests.Session()
retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

otp_cache_dict = {}
token_cache_dict = {}
data_lock = threading.Lock()
executor = ThreadPoolExecutor(max_workers=50)

# ==================== إدارة قاعدة البيانات المحلية ومقاومة النوم ====================
def load_user_db():
    with data_lock:
        try:
            if os.path.exists(USER_DATA_FILE):
                with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
        except Exception as e:
            logging.error(f"Error loading user DB: {e}", exc_info=True)
        return {}

def save_user_db(db):
    with data_lock:
        try:
            temp_file = f"{USER_DATA_FILE}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(db, f, ensure_ascii=False, indent=2)
            os.replace(temp_file, USER_DATA_FILE)
        except Exception as e:
            logging.error(f"Error saving user DB: {e}", exc_info=True)

def set_user_state(chat_id, state):
    db = load_user_db()
    if str(chat_id) not in db:
        db[str(chat_id)] = {}
    db[str(chat_id)]['state'] = state
    save_user_db(db)

def set_user_phone(chat_id, phone):
    db = load_user_db()
    if str(chat_id) not in db:
        db[str(chat_id)] = {}
    db[str(chat_id)]['phone'] = phone
    save_user_db(db)

def set_user_session(chat_id, token, phone, display_phone):
    db = load_user_db()
    db[str(chat_id)] = {
        'state': "LOGGED_IN",
        'phone': phone,
        'session': {
            'token': token,
            'phone': phone,
            'display_phone': display_phone
        }
    }
    save_user_db(db)

def delete_user_session(chat_id):
    db = load_user_db()
    if str(chat_id) in db:
        db[str(chat_id)].pop('session', None)
        db[str(chat_id)]['state'] = "WAITING_PHONE"
    save_user_db(db)

# ==================== دوال الملفات المساعدة المتبقية ====================
def load_json_file(filename, default=None):
    if default is None: default = []
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else default
    except:
        return default
    return default

def save_json_file(filename, data):
    try:
        temp_file = f"{filename}.tmp"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(temp_file, filename)
        return True
    except Exception as e:
        logging.error(f"خطأ في حفظ {filename}: {e}")
        return False

def add_user_to_db(user_id, username):
    users = load_json_file(REGISTERED_USERS_FILE, [])
    migrated_users = []
    for u in users:
        if isinstance(u, dict):
            migrated_users.append(u)
        elif isinstance(u, int):
            migrated_users.append({'id': u, 'username': 'unknown', 'date': datetime.now().strftime("%Y-%m-%d")})
    
    exists = any(str(u.get('id')) == str(user_id) for u in migrated_users)
    if not exists:
        migrated_users.append({'id': user_id, 'username': username or 'No Username', 'date': datetime.now().strftime("%Y-%m-%d")})
        save_json_file(REGISTERED_USERS_FILE, migrated_users)

def clean_expired_cache():
    current_time = time.time()
    for k, v in list(otp_cache_dict.items()):
        if isinstance(v, dict) and current_time - v.get('timestamp', 0) > 60:
            otp_cache_dict.pop(k, None)
    for k, v in list(token_cache_dict.items()):
        if isinstance(v, dict) and current_time - v.get('timestamp', 0) > 3600:
            token_cache_dict.pop(k, None)

def format_num(phone):
    phone = re.sub(r'\D', '', str(phone))
    if phone.startswith('0'):
        return "213" + phone[1:]
    if not phone.startswith('213'):
        return "213" + phone
    return phone

def format_phone(phone):
    if phone.startswith('0'): return phone
    return "0" + phone[3:]

def mask_phone(phone):
    if len(phone) >= 10: return phone[:4] + "****" + phone[-2:]
    return phone

def generate_random_djezzy_no():
    prefix = random.choice(["077", "078", "079"])
    return prefix + "".join([str(random.randint(0, 9)) for _ in range(7)])

# ==================== استدعاءات API جيزي (مطابقة تماماً لسكريبتك الشغال) ====================
def request_otp(msisdn):
    clean_expired_cache()
    cache_key = f"otp_{msisdn}"
    if cache_key in otp_cache_dict: return True

    url = f"{BASE_URL}/oauth2/registration?msisdn={msisdn}&client_id={CLIENT_ID}&scope=smsotp"
    payload = {"consent-agreement": [{"marketing-notifications": False}], "is-consent": True}
    
    for _ in range(3):
        try:
            response = session.post(url, json=payload, headers=HEADERS, proxies=PROXIES, timeout=12)
            if response.status_code in [200, 201, 202]:
                otp_cache_dict[cache_key] = {'timestamp': time.time()}
                return True
            time.sleep(0.5)
        except:
            time.sleep(0.5)
    return False

def login_with_otp(msisdn, otp):
    clean_expired_cache()
    cache_key = f"token_{msisdn}_{otp}"
    if cache_key in token_cache_dict: return token_cache_dict[cache_key]['token']

    url = f"{BASE_URL}/oauth2/token"
    payload = {
        'otp': otp,
        'mobileNumber': msisdn,
        'scope': "djezzyAppV2",
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': "mobile"
    }
    
    for _ in range(3):
        try:
            res = session.post(url, data=payload, headers={'User-Agent': "MobileApp/3.0.0"}, proxies=PROXIES, timeout=12)
            if res.status_code == 200:
                token = f"Bearer {res.json().get('access_token')}"
                token_cache_dict[cache_key] = {'token': token, 'timestamp': time.time()}
                return token
            time.sleep(0.5)
        except:
            time.sleep(0.5)
    return None

def get_sim_info(token):
    try:
        url = f"{BASE_URL}/api/v1/account/summary"
        response = session.get(url, headers={**HEADERS, 'authorization': token}, proxies=PROXIES, timeout=10)
        if response.status_code == 200:
            data = response.json()
            balance = data.get('balance', {}).get('availableBalance', 'غير معروف')
            msisdn = data.get('msisdn', 'غير معروف')
            packages = data.get('activePackages', [])
            package_list = [{'name': p.get('name', ''), 'expiry': p.get('expiryDate', '')} for p in packages]
            return {'balance': balance, 'msisdn': msisdn, 'packages': package_list}
    except Exception as e:
        logging.error(f"خطأ في جلب معلومات الشريحة: {e}")
    return None

def get_balance(token, phone):
    try:
        response_main = session.get(f"{BASE_URL}/api/v1/subscribers/main-balance/{phone}", headers={**HEADERS, 'authorization': token}, proxies=PROXIES, timeout=12)
        if response_main.status_code == 200:
            data = response_main.json()
            balance = data.get('data', {}).get('mainBalance', 0)
            due = data.get('data', {}).get('due', 0)
            return True, f"💰 الرصيد: <b>{balance:,.2f} DA</b>\n📅 متبقي: <b>{due} يوم</b>"
        return False, "❌ فشل جلب الرصيد"
    except:
        return False, "❌ خطأ في الاتصال بالسيرفر"

def activate_2go(token, phone):
    url = f"{BASE_URL}/api/v1/services/walk/activate-reward/{phone}"
    payload = {"packageCode": "GIFTWALKWIN2GO"}
    try:
        r = session.post(url, json=payload, headers={**HEADERS, 'authorization': token}, proxies=PROXIES, timeout=10)
        if r.status_code in [200, 201, 202]: return True, None
        try:
            err = r.json().get('message') or r.json().get('error') or r.text
        except:
            err = r.text
        return False, err
    except Exception as e:
        return False, str(e)

def activate_product_offer(token, phone, package_code):
    url = f"{BASE_URL}/api/v1/subscribers/activate-product/{phone}"
    payload = {"packageCode": package_code}
    try:
        response = session.post(url, json=payload, headers={**HEADERS, 'authorization': token}, proxies=PROXIES, timeout=12)
        if response.status_code in [200, 201, 202]: return True, None
        try:
            err = response.json().get('message') or response.json().get('error') or response.text
        except:
            err = response.text
        return False, err
    except Exception as e:
        return False, str(e)

# ==================== نظام MGM ====================
def send_invitation(token, sender, receiver):
    try:
        inv = session.post(f"{BASE_URL}/api/v1/services/mgm/send-invitation/{sender}", json={"msisdnReciever": receiver}, headers={**HEADERS, 'authorization': token}, proxies=PROXIES, timeout=10)
        return inv.status_code in [200, 201]
    except: return False

def get_invitations(token, msisdn):
    try:
        res = session.get(f"{BASE_URL}/api/v1/services/mgm/invitations/{msisdn}", headers={**HEADERS, "authorization": token}, proxies=PROXIES, timeout=10)
        if res.status_code == 200:
            return [inv for inv in res.json().get("data", {}).get("invitations", []) if inv.get("status") == "PENDING"]
    except: pass
    return []

def delete_invitation(token, msisdn, receiver):
    try:
        session.post(f"{BASE_URL}/api/v1/services/mgm/delete-invitation/{msisdn}", json={"msisdnReceiver": receiver}, headers={**HEADERS, "authorization": token}, proxies=PROXIES, timeout=10)
    except: pass

def activate_reward_mgm(token, msisdn):
    try:
        res = session.post(f"{BASE_URL}/api/v1/services/mgm/activate-reward/{msisdn}", json={"packageCode": "MGMBONUS1Go"}, headers={**HEADERS, "authorization": token}, proxies=PROXIES, timeout=10)
        data = res.json() if res.status_code in [200, 201] else {}
        msg = data.get("message", {})
        ar = msg.get("ar", "") if isinstance(msg, dict) else str(msg)
        return res.status_code in [200, 201], ar or "تم التفعيل"
    except: return False, "خطأ في الاتصال"

def handle_mgm_flow(chat_id, token, phone):
    try:
        ok, msg = activate_reward_mgm(token, phone)
        if ok:
            bot.send_message(chat_id, f"🎉 تم تفعيل مكافأة MGM بنجاح!\n{msg}")
            return True

        invitations = get_invitations(token, phone)
        for inv in invitations:
            receiver = inv.get("msisdnReceiver") or ""
            if receiver:
                delete_invitation(token, phone, receiver)
                time.sleep(0.5)

        for _ in range(20):
            target = generate_random_djezzy_no()
            target_f = format_num(target)
            if send_invitation(token, phone, target_f):
                time.sleep(0.5)
                ok, _ = activate_reward_mgm(token, phone)
                if ok:
                    registered = load_json_file(REGISTERED_NUMBERS_FILE, [])
                    registered.append({"sender": phone, "target": target, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "offer": "MGM", "user_id": chat_id})
                    save_json_file(REGISTERED_NUMBERS_FILE, registered)
                    bot.send_message(chat_id, "🎉 تم تفعيل مكافأة MGM بنجاح! (1GB إضافي)")
                    return True
                delete_invitation(token, phone, target_f)
                time.sleep(0.5)
        bot.send_message(chat_id, "❌ وصلت للحد الأقصى من الدعوات اليومي. حاول غداً.")
    except Exception as e:
        logging.error(f"خطأ في MGM: {e}")
        bot.send_message(chat_id, "❌ حدث خطأ أثناء معالجة الدعوات.")

# ==================== قنوات الاشتراك والتحقق ====================
def get_unjoined_channels(user_id):
    if user_id == ADMIN_ID: return []
    channels = load_json_file(CHANNELS_FILE, [])
    unjoined = []
    for ch in channels:
        try:
            member = bot.get_chat_member(ch['username'], user_id)
            if member.status in ['left', 'kicked', 'None', None]:
                unjoined.append(ch)
        except:
            unjoined.append(ch)
    return unjoined

def check_must_join(user_id):
    return len(get_unjoined_channels(user_id)) == 0

def send_join_msg(chat_id):
    unjoined_channels = get_unjoined_channels(chat_id)
    if not unjoined_channels: return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for ch in unjoined_channels:
        markup.add(types.InlineKeyboardButton(text=ch.get('title', 'قناة'), url=ch.get('link', '#')))
    markup.add(types.InlineKeyboardButton(text="🔄 تم الاشتراك، تأكيد ✅", callback_data="check_subscription"))
    bot.send_message(chat_id, "⚠️ <b>عذراً، يجب عليك الاشتراك في القنوات المتبقية أولاً:</b>", reply_markup=markup)

def show_main_menu(chat_id, display_phone):
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(text=off['name'][:20], callback_data=f"show_{oid}") for oid, off in ALL_OFFERS.items()]
    for i in range(0, len(buttons), 2):
        if i+1 < len(buttons): markup.add(buttons[i], buttons[i+1])
        else: markup.add(buttons[i])
    markup.add(types.InlineKeyboardButton(text="🎁 تفعيل هدايا الدعوات (MGM)", callback_data="activate_mgm"))
    markup.add(types.InlineKeyboardButton(text="💰 فحص الرصيد", callback_data="balance"))
    markup.add(types.InlineKeyboardButton(text="📱 معلومات الشريحة", callback_data="sim_info"))
    markup.add(types.InlineKeyboardButton(text="🔄 تسجيل خروج", callback_data="logout"))
    
    bot.send_message(chat_id, f"✨ <b>مرحباً بك في بوت عروض جيزي المتكامل</b> ✨\n\n📱 الرقم النشط: <code>{mask_phone(display_phone)}</code>\n\nاختر العرض أو الخدمة:", reply_markup=markup)

# ==================== أوامر ومعالجات الرسائل ====================
@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    add_user_to_db(chat_id, message.from_user.username)
    
    if MAINTENANCE_MODE:
        bot.send_message(chat_id, MAINTENANCE_MESSAGE)
        return
    if not check_must_join(chat_id):
        send_join_msg(chat_id)
        return

    db = load_user_db()
    user_info = db.get(str(chat_id), {})
    session_data = user_info.get('session')

    if session_data:
        show_main_menu(chat_id, session_data['display_phone'])
    else:
        set_user_state(chat_id, "WAITING_PHONE")
        bot.send_message(chat_id, "✨ <b>مرحباً بك في بوت عروض جيزي</b> ✨\n\n📲 يرجى إرسال رقم هاتفك (07XXXXXXXX) للبدء:")

@bot.message_handler(commands=['info'])
def info_command(message):
    chat_id = message.chat.id
    db = load_user_db()
    user_info = db.get(str(chat_id), {})
    session_data = user_info.get('session')

    if not session_data:
        bot.send_message(chat_id, "⚠️ يرجى تسجيل الدخول أولاً عبر /start")
        return
    
    token = session_data['token']
    sim_info = get_sim_info(token)
    if not sim_info:
        bot.send_message(chat_id, "❌ فشل جلب معلومات الشريحة.")
        return
    packages_str = "".join([f"📦 {p['name']} (ينتهي في: {p['expiry']})\n" for p in sim_info['packages']]) or "لا توجد عروض نشطة."
    bot.send_message(chat_id, f"📱 <b>معلومات الشريحة:</b>\n👤 الرقم: <code>{sim_info['msisdn']}</code>\n💰 الرصيد المتوفر: <b>{sim_info['balance']} DA</b>\n\n<b>📦 العروض النشطة:</b>\n{packages_str}")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    chat_id = message.chat.id
    text = message.text.strip()
    
    if MAINTENANCE_MODE:
        bot.send_message(chat_id, MAINTENANCE_MESSAGE)
        return
    if not check_must_join(chat_id):
        send_join_msg(chat_id)
        return
    
    db = load_user_db()
    user_info = db.get(str(chat_id), {})
    state = user_info.get('state')
    session_data = user_info.get('session')

    if session_data:
        bot.send_message(chat_id, "⚠️ يرجى استخدام القائمة التفاعلية بالضغط على الأزرار بالأسفل.")
        return
        
    if state == "WAITING_PHONE" or state is None:
        formatted = format_num(text)
        if len(formatted) == 12 and formatted.startswith("2137"):
            bot.send_message(chat_id, "⏳ جاري إرسال رمز التحقق (OTP)...")
            if request_otp(formatted):
                set_user_phone(chat_id, formatted)
                set_user_state(chat_id, "WAITING_OTP")
                bot.send_message(chat_id, f"📥 تم إرسال الرمز إلى <code>{mask_phone(text)}</code>.\n\nالرجاء إدخال الرمز المكون من 6 أرقام:")
            else:
                bot.send_message(chat_id, "❌ فشل إرسال الرمز. يرجى التأكد من الرقم والمحاولة لاحقاً.")
        else:
            bot.send_message(chat_id, "❌ الرقم غير صحيح! يرجى إدخال رقم جيزي صالح يبدأ بـ 07.")
    
    elif state == "WAITING_OTP":
        if text.isdigit() and len(text) == 6:
            msisdn = user_info.get('phone')
            if not msisdn:
                bot.send_message(chat_id, "⚠️ حدث خطأ، يرجى إعادة إرسال الرقم من جديد:")
                set_user_state(chat_id, "WAITING_PHONE")
                return
            
            bot.send_message(chat_id, "⏳ جاري تسجيل الدخول وحفظ الجلسة...")
            token = login_with_otp(msisdn, text)
            if token:
                display_phone = format_phone(msisdn)
                set_user_session(chat_id, token, msisdn, display_phone)
                bot.send_message(chat_id, "✅ تم تسجيل الدخول بنجاح!")
                show_main_menu(chat_id, display_phone)
            else:
                bot.send_message(chat_id, "❌ الرمز الذي أدخلته خاطئ أو منتهي الصلاحية. حاول مجدداً:")
        else:
            bot.send_message(chat_id, "⚠️ يرجى كتابة الرمز المكون من 6 أرقام بشكل صحيح:")

# ==================== معالجات الـ Callbacks ====================
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    data = call.data
    
    if data == "check_subscription":
        if check_must_join(chat_id):
            bot.answer_callback_query(call.id, "✅ تم التحقق بنجاح!")
            bot.send_message(chat_id, "🎉 شكراً لك على الاشتراك! أرسل /start للبدء.")
        else:
            bot.answer_callback_query(call.id, "❌ لم تشترك في جميع القنوات بعد!", show_alert=True)
        return
        
    db = load_user_db()
    user_info = db.get(str(chat_id), {})
    session_data = user_info.get('session')

    if not session_data:
        bot.answer_callback_query(call.id, "⚠️ انتهت جلستك، يرجى تسجيل الدخول مجدداً عبر /start", show_alert=True)
        return
        
    token = session_data['token']
    phone = session_data['phone']
    
    if data.startswith("show_"):
        offer_id = data.replace("show_", "")
        offer = ALL_OFFERS.get(offer_id)
        if offer:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("✅ تأكيد التفعيل", callback_data=f"activate_{offer_id}"), types.InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_menu"))
            bot.edit_message_text(f"ℹ️ <b>تفاصيل العرض:</b>\n\n📌 الاسم: <b>{offer['name']}</b>\n📦 الحجم: <b>{offer['amount']}</b>\n💰 السعر: <b>{offer['price']}</b>\n📅 الصلاحية: <b>{offer['duration']}</b>\n\n⚠️ هل تريد بالتأكيد تفعيل هذا العرض؟", chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
    
    elif data.startswith("activate_"):
        offer_id = data.replace("activate_", "")
        if offer_id == "mgm":
            bot.answer_callback_query(call.id, "⏳ جاري تشغيل نظام الدعوات...")
            bot.send_message(chat_id, "⚡ جاري العمل على نظام الدعوات الخاص بك وتفعيل الـ 1GB، قد يستغرق الأمر دقيقة...")
            threading.Thread(target=handle_mgm_flow, args=(chat_id, token, phone)).start()
            return
            
        offer = ALL_OFFERS.get(offer_id)
        if offer:
            bot.answer_callback_query(call.id, "⏳ جاري تفعيل العرض...")
            success, err = activate_2go(token, phone) if offer['offer_id'] == 'offer_1' else activate_product_offer(token, phone, offer['code'])
            if success:
                bot.send_message(chat_id, f"🎉 <b>تم تفعيل عرض {offer['name']} بنجاح!</b>")
                registered = load_json_file(REGISTERED_NUMBERS_FILE, [])
                registered.append({"phone": phone, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "offer": offer['name'], "user_id": chat_id})
                save_json_file(REGISTERED_NUMBERS_FILE, registered)
            else:
                bot.send_message(chat_id, f"❌ <b>فشل تفعيل العرض.</b>\nالسبب: {err}")
    
    elif data == "balance":
        bot.answer_callback_query(call.id, "⏳ جاري جلب الرصيد...")
        _, msg = get_balance(token, phone)
        bot.send_message(chat_id, msg)
        
    elif data == "sim_info":
        bot.answer_callback_query(call.id, "⏳ جاري جلب المعلومات...")
        sim_info = get_sim_info(token)
        if sim_info:
            packages_str = "".join([f"📦 {p['name']} (ينتهي في: {p['expiry']})\n" for p in sim_info['packages']]) or "لا توجد عروض نشطة."
            bot.send_message(chat_id, f"📱 <b>معلومات الشريحة:</b>\n👤 الرقم: <code>{sim_info['msisdn']}</code>\n💰 الرصيد المتوفر: <b>{sim_info['balance']} DA</b>\n\n<b>📦 العروض النشطة:</b>\n{packages_str}")
        else:
            bot.send_message(chat_id, "❌ فشل جلب معلومات الشريحة.")
            
    elif data == "logout":
        delete_user_session(chat_id)
        bot.answer_callback_query(call.id, "🔄 تم تسجيل الخروج بنجاح.")
        bot.send_message(chat_id, "🔄 تم تسجيل الخروج بنجاح. أرسل رقمك مجدداً للبدء.")
        
    elif data == "back_to_menu":
        bot.delete_message(chat_id, call.message.message_id)
        show_main_menu(chat_id, format_phone(phone))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
