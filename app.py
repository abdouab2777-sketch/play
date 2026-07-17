from flask import Flask
from threading import Thread
import logging
import requests
import random
import time
import json
import os
import re
import threading
from datetime import datetime, timedelta
import telebot
from telebot import types
import sys
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor

# ==================== التكوين الأساسي ====================
BOT_TOKEN = "8320518146:AAHNSvwvKgjH_G_YHadfPHgXqz60QrALq9s"
ADMIN_ID = 7242923713
PROOF_CHAT_ID = -1004477473385
MAINTENANCE_MODE = False
MAINTENANCE_MESSAGE = "⚠️ البوت حاليا في وضع الصيانة، حاول لاحقا."

# ==================== تعريف البوت فوراً ====================
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ==================== البروكسي (معطل) ====================
USE_PROXY = False
PROXIES = None

# ==================== العروض المتاحة ====================
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

# ==================== الإعدادات ====================
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

# ==================== الملفات ====================
REGISTERED_NUMBERS_FILE = "registered_numbers.json"
REGISTERED_USERS_FILE = "registered_users.json"
CHANNELS_FILE = "channels.json"

# ==================== حذف جميع القنوات عند بدء التشغيل ====================
if os.path.exists(CHANNELS_FILE):
    with open(CHANNELS_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=2)
    print("✅ تم حذف جميع القنوات (تم تفريغ الملف).")
else:
    with open(CHANNELS_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=2)

# ==================== إعدادات التسجيل ====================
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.FileHandler('djezzy_bot.log'), logging.StreamHandler()]
)

# ==================== إعداد الجلسة ====================
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

# ==================== التخزين المؤقت ====================
otp_cache_dict = {}
token_cache_dict = {}
user_data = {}
user_states = {}
user_sessions = {}
user_numbers = {}
pending_otp = {}
data_lock = threading.Lock()

# ==================== ThreadPool ====================
executor = ThreadPoolExecutor(max_workers=50)

# ==================== دوال الملفات ====================
def load_json_file(filename, default=None):
    if default is None:
        default = []
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, list):
                    return default
                return data
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
    if not users:
        users = []
    elif isinstance(users[0], int):
        new_users = []
        for u in users:
            if isinstance(u, int):
                new_users.append({'id': u, 'username': 'unknown', 'date': datetime.now().strftime("%Y-%m-%d")})
        users = new_users
        save_json_file(REGISTERED_USERS_FILE, users)
    
    exists = False
    for u in users:
        if isinstance(u, dict) and str(u.get('id')) == str(user_id):
            exists = True
            break
        elif isinstance(u, int) and u == user_id:
            exists = True
            break
    
    if not exists:
        users.append({'id': user_id, 'username': username or 'No Username', 'date': datetime.now().strftime("%Y-%m-%d")})
        save_json_file(REGISTERED_USERS_FILE, users)

# ==================== دوال مساعدة ====================
def clean_expired_cache():
    current_time = time.time()
    for k, v in list(otp_cache_dict.items()):
        if current_time - v.get('timestamp', 0) > 60:
            otp_cache_dict.pop(k, None)
    for k, v in list(token_cache_dict.items()):
        if current_time - v.get('timestamp', 0) > 3600:
            token_cache_dict.pop(k, None)

def format_num(phone):
    phone = re.sub(r'\D', '', str(phone))
    if phone.startswith('0'):
        return "213" + phone[1:]
    if not phone.startswith('213'):
        return "213" + phone
    return phone

def format_phone(phone):
    if phone.startswith('0'):
        return phone
    return "0" + phone[3:]

def mask_phone(phone):
    if len(phone) >= 10:
        return phone[:4] + "****" + phone[-2:]
    return phone

def get_user_tag(message):
    u = message.from_user
    return f"@{u.username}" if u.username else u.first_name or "User"

def generate_random_djezzy_no():
    prefix = random.choice(["077", "078", "079"])
    return prefix + "".join([str(random.randint(0, 9)) for _ in range(7)])

# ==================== دوال API الأساسية ====================
def request_otp(msisdn):
    clean_expired_cache()
    cache_key = f"otp_{msisdn}"
    if cache_key in otp_cache_dict:
        return True

    url = f"{BASE_URL}/oauth2/registration"
    params = {'msisdn': msisdn, 'client_id': CLIENT_ID, 'scope': "smsotp"}
    payload = {"consent-agreement": [{"marketing-notifications": False}], "is-consent": True}
    
    for attempt in range(3):
        try:
            response = session.post(url, params=params, json=payload, headers=HEADERS, proxies=PROXIES, timeout=12)
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
    if cache_key in token_cache_dict:
        return token_cache_dict[cache_key]['token']

    url = f"{BASE_URL}/oauth2/token"
    payload = {
        'otp': otp,
        'mobileNumber': msisdn,
        'scope': "djezzyAppV2",
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': "mobile"
    }
    
    for attempt in range(3):
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
        headers_with_auth = {**HEADERS, 'authorization': token}
        response = session.get(url, headers=headers_with_auth, proxies=PROXIES, timeout=10)
        if response.status_code == 200:
            data = response.json()
            balance = data.get('balance', {}).get('availableBalance', 'غير معروف')
            msisdn = data.get('msisdn', 'غير معروف')
            packages = data.get('activePackages', [])
            package_list = []
            for p in packages:
                name = p.get('name', '')
                expiry = p.get('expiryDate', '')
                package_list.append({'name': name, 'expiry': expiry})
            return {
                'balance': balance,
                'msisdn': msisdn,
                'packages': package_list
            }
    except Exception as e:
        logging.error(f"خطأ في جلب معلومات الشريحة: {e}")
    return None

def get_balance(token, phone):
    try:
        headers_with_auth = {**HEADERS, 'authorization': token}
        response_main = session.get(f"{BASE_URL}/api/v1/subscribers/main-balance/{phone}", headers=headers_with_auth, proxies=PROXIES, timeout=12)
        if response_main.status_code == 200:
            data = response_main.json()
            balance = data.get('data', {}).get('mainBalance', 0)
            due = data.get('data', {}).get('due', 0)
            return True, f"💰 الرصيد: <b>{balance:,.2f} DA</b>\n📅 متبقي: <b>{due} يوم</b>"
        return False, "❌ فشل جلب الرصيد"
    except:
        return False, "❌ خطأ في الاتصال بالسيرفر"

# ==================== دوال التفعيل المتقدمة ====================
def activate_2go(token, phone):
    url = f"{BASE_URL}/api/v1/services/walk/activate-reward/{phone}"
    payload = {"packageCode": "GIFTWALKWIN2GO"}
    try:
        r = session.post(url, json=payload, headers={**HEADERS, 'authorization': token}, proxies=PROXIES, timeout=10)
        if r.status_code in [200, 201, 202]:
            return True, None
        else:
            try:
                error_json = r.json()
                error_msg = error_json.get('message') or error_json.get('error') or r.text
            except:
                error_msg = r.text
            return False, error_msg
    except Exception as e:
        return False, str(e)

def activate_product_offer(token, phone, package_code):
    url = f"{BASE_URL}/api/v1/subscribers/activate-product/{phone}"
    payload = {"packageCode": package_code}
    try:
        headers_with_auth = {**HEADERS, 'authorization': token}
        response = session.post(url, json=payload, headers=headers_with_auth, proxies=PROXIES, timeout=12)
        if response.status_code in [200, 201, 202]:
            return True, None
        else:
            try:
                error_json = response.json()
                error_msg = error_json.get('message') or error_json.get('error') or response.text
            except:
                error_msg = response.text
            return False, error_msg
    except Exception as e:
        return False, str(e)

# ==================== دوال نظام الدعوات (MGM) ====================
def send_invitation(token, sender, receiver):
    try:
        inv = session.post(
            f"{BASE_URL}/api/v1/services/mgm/send-invitation/{sender}",
            json={"msisdnReciever": receiver},
            headers={**HEADERS, 'authorization': token},
            proxies=PROXIES,
            timeout=10
        )
        return inv.status_code in [200, 201]
    except:
        return False

def get_invitations(token, msisdn):
    try:
        headers = {**HEADERS, "authorization": token}
        res = session.get(f"{BASE_URL}/api/v1/services/mgm/invitations/{msisdn}", headers=headers, proxies=PROXIES, timeout=10)
        if res.status_code == 200:
            all_inv = res.json().get("data", {}).get("invitations", [])
            return [inv for inv in all_inv if inv.get("status") == "PENDING"]
    except:
        pass
    return []

def delete_invitation(token, msisdn, receiver):
    try:
        headers = {**HEADERS, "authorization": token}
        session.post(f"{BASE_URL}/api/v1/services/mgm/delete-invitation/{msisdn}", json={"msisdnReceiver": receiver}, headers=headers, proxies=PROXIES, timeout=10)
    except:
        pass

def activate_reward_mgm(token, msisdn):
    try:
        headers = {**HEADERS, "authorization": token}
        res = session.post(f"{BASE_URL}/api/v1/services/mgm/activate-reward/{msisdn}", json={"packageCode": "MGMBONUS1Go"}, headers=headers, proxies=PROXIES, timeout=10)
        data = res.json() if res.status_code in [200, 201] else {}
        msg = data.get("message", {})
        ar = msg.get("ar", "") if isinstance(msg, dict) else str(msg)
        if res.status_code in [200, 201]:
            return True, ar or "تم التفعيل"
        return False, ar or "لا توجد مكافأة"
    except:
        return False, "خطأ في الاتصال"

def register_random(receiver):
    try:
        session.post(f"{BASE_URL}/oauth2/registration?msisdn={receiver}&client_id={CLIENT_ID}&scope=smsotp", 
                     json={"consent-agreement": [{"marketing-notifications": False}], "is-consent": True}, 
                     headers=HEADERS, proxies=PROXIES, timeout=10)
    except:
        pass

def handle_mgm_flow(chat_id, token, phone, message):
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
                register_random(target_f)
                time.sleep(0.5)
                
                ok, _ = activate_reward_mgm(token, phone)
                if ok:
                    number_data = {
                        "sender": phone,
                        "target": target,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "offer": "MGM",
                        "user_id": chat_id
                    }
                    registered = load_json_file(REGISTERED_NUMBERS_FILE, [])
                    registered.append(number_data)
                    save_json_file(REGISTERED_NUMBERS_FILE, registered)
                    
                    bot.send_message(chat_id, "🎉 تم تفعيل مكافأة MGM بنجاح! (1GB إضافي)")
                    return True
                
                delete_invitation(token, phone, target_f)
                time.sleep(0.5)
        
        bot.send_message(chat_id, "❌ وصلت للحد الأقصى من الدعوات اليومي. حاول غداً.")
        return False
        
    except Exception as e:
        logging.error(f"خطأ في MGM: {e}")
        bot.send_message(chat_id, "❌ حدث خطأ أثناء معالجة الدعوات.")
        return False

# ==================== نظام الاشتراك الديناميكي ====================
def get_unjoined_channels(user_id):
    if user_id == ADMIN_ID:
        return []
    channels = load_json_file(CHANNELS_FILE, [])
    if not channels:
        return []
    unjoined = []
    for ch in channels:
        try:
            member = bot.get_chat_member(ch['username'], user_id)
            if member.status in ['left', 'kicked', 'None', None]:
                unjoined.append(ch)
        except Exception:
            unjoined.append(ch)
    return unjoined

def check_must_join(user_id):
    return len(get_unjoined_channels(user_id)) == 0

def send_join_msg(chat_id):
    unjoined_channels = get_unjoined_channels(chat_id)
    if not unjoined_channels:
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for ch in unjoined_channels:
        markup.add(types.InlineKeyboardButton(text=ch.get('title', 'قناة'), url=ch.get('link', '#')))
    markup.add(types.InlineKeyboardButton(text="🔄 تم الاشتراك، تأكيد ✅", callback_data="check_subscription"))
    bot.send_message(chat_id, "⚠️ <b>عذراً، يجب عليك الاشتراك في القنوات المتبقية أولاً:</b>", reply_markup=markup)

# ==================== واجهات البوت ====================
def get_final_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("📢 @hellyeah619dz", url="https://t.me/hellyeah619dz"))
    return keyboard

def show_main_menu(chat_id, display_phone):
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for off_id, off_info in ALL_OFFERS.items():
        buttons.append(types.InlineKeyboardButton(text=off_info['name'][:20], callback_data=f"show_{off_id}"))
    for i in range(0, len(buttons), 2):
        if i+1 < len(buttons):
            markup.add(buttons[i], buttons[i+1])
        else:
            markup.add(buttons[i])
    markup.add(types.InlineKeyboardButton(text="🎁 تفعيل هدايا الدعوات (MGM)", callback_data="activate_mgm"))
    markup.add(types.InlineKeyboardButton(text="💰 فحص الرصيد", callback_data="balance"))
    markup.add(types.InlineKeyboardButton(text="📱 معلومات الشريحة", callback_data="sim_info"))
    markup.add(types.InlineKeyboardButton(text="🔄 تسجيل خروج", callback_data="logout"))
    msg_text = f"✨ <b>مرحباً بك في بوت عروض جيزي المتكامل</b> ✨\n\n📱 الرقم النشط: <code>{mask_phone(display_phone)}</code>\n\nاختر العرض أو الخدمة:"
    bot.send_message(chat_id, msg_text, reply_markup=markup)

# ==================== أوامر البوت ====================
@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    username = message.from_user.username or "No Username"
    add_user_to_db(chat_id, username)
    
    if MAINTENANCE_MODE:
        bot.send_message(chat_id, MAINTENANCE_MESSAGE)
        return

    if not check_must_join(chat_id):
        send_join_msg(chat_id)
        return

    if chat_id in user_sessions:
        show_main_menu(chat_id, user_sessions[chat_id]['display_phone'])
    else:
        bot.send_message(
            chat_id,
            "✨ <b>مرحباً بك في بوت عروض جيزي</b> ✨\n\n"
            "📲 يرجى إرسال رقم هاتفك (07XXXXXXXX) للبدء:"
        )

@bot.message_handler(commands=['info'])
def info_command(message):
    chat_id = message.chat.id
    if chat_id not in user_sessions:
        bot.send_message(chat_id, "⚠️ يرجى تسجيل الدخول أولاً عبر /start")
        return
    
    token = user_sessions[chat_id]['token']
    sim_info = get_sim_info(token)
    if not sim_info:
        bot.send_message(chat_id, "❌ تعذر جلب معلومات الشريحة.")
        return
    
    msg = (
        f"📱 <b>معلومات الشريحة</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"📞 الرقم: {sim_info.get('msisdn', 'غير معروف')}\n"
        f"💰 الرصيد: {sim_info.get('balance', 'غير معروف')} دج\n"
        f"━━━━━━━━━━━━━━\n"
        f"🎁 <b>الباقات النشطة:</b>\n"
    )
    pkgs = sim_info.get('packages', [])
    if pkgs:
        for p in pkgs:
            name = p.get('name', '')
            expiry = p.get('expiry', '')
            if expiry:
                try:
                    exp_date = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
                    now = datetime.now(exp_date.tzinfo)
                    remaining = exp_date - now
                    days = remaining.days
                    hours = remaining.seconds // 3600
                    time_left = f"{days} يوم {hours} ساعة" if days > 0 else f"{hours} ساعة"
                    msg += f"• {name} (تنتهي بعد {time_left})\n"
                except:
                    msg += f"• {name} (تنتهي: {expiry})\n"
            else:
                msg += f"• {name}\n"
    else:
        msg += "لا توجد باقات نشطة.\n"
    
    bot.send_message(chat_id, msg)

@bot.message_handler(commands=['cancel'])
def cancel_command(message):
    chat_id = message.chat.id
    user_numbers.pop(chat_id, None)
    pending_otp.pop(chat_id, None)
    bot.send_message(chat_id, "❌ تم الإلغاء")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("➕ إضافة قناة", callback_data="adm_add"),
        types.InlineKeyboardButton("❌ حذف قناة", callback_data="adm_del"),
        types.InlineKeyboardButton("📊 الإحصائيات", callback_data="adm_stats")
    )
    bot.send_message(ADMIN_ID, "🛠️ <b>لوحة تحكم الأدمن</b>", reply_markup=markup)

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    if message.from_user.id != ADMIN_ID:
        return
    text_to_send = message.text.split(maxsplit=1)
    if len(text_to_send) < 2:
        bot.send_message(message.chat.id, "❌ استعمل: /broadcast رسالة هنا")
        return
    users = load_json_file(REGISTERED_USERS_FILE, [])
    sent_count = 0
    for u in users:
        try:
            user_id = u.get('id') if isinstance(u, dict) else u
            bot.send_message(user_id, text_to_send[1])
            sent_count += 1
            time.sleep(0.05)
        except:
            continue
    bot.send_message(message.chat.id, f"✅ تم الإرسال إلى {sent_count} مستخدم")

@bot.message_handler(commands=['stats'])
def stats_command(message):
    if message.from_user.id != ADMIN_ID:
        return
    users = load_json_file(REGISTERED_USERS_FILE, [])
    numbers = load_json_file(REGISTERED_NUMBERS_FILE, [])
    channels = load_json_file(CHANNELS_FILE, [])
    stats_text = (
        f"📊 <b>إحصائيات البوت</b>\n\n"
        f"👥 المستخدمين: <b>{len(users)}</b>\n"
        f"✅ التفعيلات: <b>{len(numbers)}</b>\n"
        f"📢 القنوات: <b>{len(channels)}</b>"
    )
    bot.send_message(ADMIN_ID, stats_text)

@bot.message_handler(commands=['maintenance'])
def maintenance_command(message):
    global MAINTENANCE_MODE
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "❌ استخدم /maintenance on/off")
        return
    MAINTENANCE_MODE = args[1].lower() == 'on'
    bot.send_message(message.chat.id, f"✅ وضع الصيانة: {'مفعل' if MAINTENANCE_MODE else 'معطل'}")

# ==================== معالجة الكولباك ====================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    data = call.data

    if data.startswith("adm_") or data.startswith("delch_"):
        if user_id != ADMIN_ID:
            return
        bot.answer_callback_query(call.id)
        if data == "adm_stats":
            users = load_json_file(REGISTERED_USERS_FILE, [])
            numbers = load_json_file(REGISTERED_NUMBERS_FILE, [])
            channels = load_json_file(CHANNELS_FILE, [])
            stats_text = f"📊 <b>الإحصائيات</b>\n\n👥 المستخدمين: {len(users)}\n✅ التفعيلات: {len(numbers)}\n📢 القنوات: {len(channels)}"
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 عودة", callback_data="adm_back"))
            bot.edit_message_text(stats_text, ADMIN_ID, call.message.message_id, reply_markup=markup)
        elif data == "adm_add":
            msg = bot.send_message(ADMIN_ID, "📥 أرسل رابط القناة:")
            bot.register_next_step_handler(msg, process_add_channel)
        elif data == "adm_del":
            channels = load_json_file(CHANNELS_FILE, [])
            if not channels:
                bot.send_message(ADMIN_ID, "❌ لا توجد قنوات.")
                return
            markup = types.InlineKeyboardMarkup(row_width=1)
            for idx, ch in enumerate(channels):
                markup.add(types.InlineKeyboardButton(f"❌ {ch.get('title', 'قناة')}", callback_data=f"delch_{idx}"))
            markup.add(types.InlineKeyboardButton("🔙 عودة", callback_data="adm_back"))
            bot.edit_message_text("🗑️ اضغط على القناة لحذفها:", ADMIN_ID, call.message.message_id, reply_markup=markup)
        elif data == "adm_back":
            admin_panel(call.message)
        elif data.startswith("delch_"):
            idx = int(data.replace("delch_", ""))
            channels = load_json_file(CHANNELS_FILE, [])
            if 0 <= idx < len(channels):
                removed = channels.pop(idx)
                save_json_file(CHANNELS_FILE, channels)
                bot.answer_callback_query(call.id, f"✅ تم حذف {removed.get('title', 'القناة')}")
                admin_panel(call.message)
        return

    if data == "check_subscription":
        if check_must_join(user_id):
            bot.answer_callback_query(call.id, "✅ شكراً للاشتراك!")
            bot.delete_message(user_id, call.message.message_id)
            start_command(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ لم تشترك في كل القنوات بعد!", show_alert=True)
            bot.delete_message(user_id, call.message.message_id)
            send_join_msg(user_id)
        return

    if data == "resend_otp":
        if user_id in user_numbers:
            bot.answer_callback_query(call.id, "🔄 جاري إعادة الإرسال...")
            phone_data = user_numbers[user_id]
            if request_otp(phone_data['formatted']):
                bot.edit_message_text("✅ تم إعادة إرسال الرمز.\nأدخل الرمز المكون من 6 أرقام:", user_id, call.message.message_id)
            else:
                bot.send_message(user_id, "❌ فشل إعادة الإرسال.")
        return

    if data == "cancel_otp":
        bot.answer_callback_query(call.id, "❌ تم الإلغاء")
        user_numbers.pop(user_id, None)
        pending_otp.pop(user_id, None)
        bot.delete_message(user_id, call.message.message_id)
        start_command(call.message)
        return

    if not check_must_join(user_id):
        send_join_msg(user_id)
        return

    if data == "logout":
        user_sessions.pop(user_id, None)
        bot.edit_message_text("🔓 تم تسجيل الخروج.", user_id, call.message.message_id)
        return

    if user_id not in user_sessions:
        bot.answer_callback_query(call.id, "❌ انتهت الجلسة، أرسل /start", show_alert=True)
        return

    session = user_sessions[user_id]

    if data == "activate_mgm":
        bot.answer_callback_query(call.id, "🔄 جاري معالجة الدعوات...")
        bot.edit_message_text("⏳ جاري تفعيل هدايا الدعوات... قد يستغرق دقيقة.", user_id, call.message.message_id)
        executor.submit(handle_mgm_flow, user_id, session['token'], session['phone'], call.message)

    elif data == "balance":
        bot.answer_callback_query(call.id, "🔄 جاري الفحص...")
        success, msg = get_balance(session['token'], session['phone'])
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 القائمة", callback_data="main_menu"))
        bot.edit_message_text(msg, user_id, call.message.message_id, reply_markup=markup)

    elif data == "sim_info":
        bot.answer_callback_query(call.id, "🔄 جاري جلب المعلومات...")
        sim_info = get_sim_info(session['token'])
        if sim_info:
            msg = (
                f"📱 <b>معلومات الشريحة</b>\n"
                f"━━━━━━━━━━━━━━\n"
                f"📞 الرقم: {sim_info.get('msisdn', 'غير معروف')}\n"
                f"💰 الرصيد: {sim_info.get('balance', 'غير معروف')} دج\n"
                f"━━━━━━━━━━━━━━\n"
                f"🎁 <b>الباقات النشطة:</b>\n"
            )
            pkgs = sim_info.get('packages', [])
            if pkgs:
                for p in pkgs:
                    msg += f"• {p.get('name', '')}\n"
            else:
                msg += "لا توجد باقات نشطة.\n"
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 القائمة", callback_data="main_menu"))
            bot.edit_message_text(msg, user_id, call.message.message_id, reply_markup=markup)
        else:
            bot.edit_message_text("❌ تعذر جلب المعلومات.", user_id, call.message.message_id)

    elif data.startswith("show_"):
        offer_id = data.replace("show_", "")
        offer = ALL_OFFERS.get(offer_id)
        if offer:
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton("✅ تأكيد التفعيل", callback_data=f"activate_{offer_id}"),
                types.InlineKeyboardButton("🔙 إلغاء", callback_data="main_menu")
            )
            details = (
                f"📋 <b>تفاصيل العرض</b>\n\n"
                f"📦 الاسم: {offer['name']}\n"
                f"💰 السعر: {offer['price']}\n"
                f"⏳ الصلاحية: {offer['duration']}\n\n"
                f"هل أنت متأكد؟"
            )
            bot.edit_message_text(details, user_id, call.message.message_id, reply_markup=markup)

    elif data.startswith("activate_"):
        offer_id = data.replace("activate_", "")
        offer = ALL_OFFERS.get(offer_id)
        bot.edit_message_text("⏳ جاري التفعيل...", user_id, call.message.message_id)
        
        if offer_id == 'offer_1':
            success, error_msg = activate_2go(session['token'], session['phone'])
        else:
            success, error_msg = activate_product_offer(session['token'], session['phone'], offer['code'])
        
        if success:
            registered = load_json_file(REGISTERED_NUMBERS_FILE, [])
            registered.append({
                'user_id': user_id,
                'phone': session['display_phone'],
                'offer': offer['name'],
                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            save_json_file(REGISTERED_NUMBERS_FILE, registered)
            
            bot.edit_message_text(
                f"🎉 <b>تم التفعيل بنجاح!</b>\n\n"
                f"📱 الرقم: {session['display_phone']}\n"
                f"📦 العرض: {offer['name']}",
                user_id, call.message.message_id,
                reply_markup=get_final_keyboard()
            )
            
            try:
                username = get_user_tag(call.message)
                proof_msg = (
                    f"⚡ <b>تفعيل ناجح!</b>\n"
                    f"👤 المستخدم: {username}\n"
                    f"📦 العرض: {offer['name']}\n"
                    f"📱 الرقم: {mask_phone(session['display_phone'])}"
                )
                bot.send_message(PROOF_CHAT_ID, proof_msg)
            except:
                pass
        else:
            if error_msg and any(kw in error_msg.lower() for kw in ['week', 'not eligible', 'not completed', 'bundle', 'غير مؤهل', 'الأسبوع']):
                bot.edit_message_text(
                    "❌ <b>لا يمكن تفعيل 2GB الآن</b>\n\n"
                    "⭐ السبب: لم يكتمل الأسبوع أو الباقة غير مؤهلة\n\n"
                    "🔴 يلزمك تفعيل باقة 100da أو أكثر خلال الأسبوع الجاري\n"
                    "📌 قم بتفعيل باقة عبر *111# ثم حاول مجدداً.",
                    user_id, call.message.message_id,
                    reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 القائمة", callback_data="main_menu"))
                )
            else:
                bot.edit_message_text(
                    f"❌ <b>فشل التفعيل</b>\n\n"
                    f"السبب: {error_msg[:200] if error_msg else 'غير معروف'}\n"
                    f"تأكد من توفر الرصيد الكافي.",
                    user_id, call.message.message_id,
                    reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 القائمة", callback_data="main_menu"))
                )

    elif data == "main_menu":
        bot.delete_message(user_id, call.message.message_id)
        show_main_menu(user_id, session['display_phone'])

# ==================== معالجة إضافة القناة ====================
def process_add_channel(message):
    if message.from_user.id != ADMIN_ID:
        return
    url = message.text.strip()
    if "t.me/" not in url:
        bot.send_message(ADMIN_ID, "❌ الرابط غير صالح!")
        return
    try:
        username_part = url.split("t.me/")[1].split("/")[0]
        ch_username = f"@{username_part}"
        chat_info = bot.get_chat(ch_username)
        ch_title = f"📢 {chat_info.title}"
        
        channels = load_json_file(CHANNELS_FILE, [])
        if ch_username in [c.get('username') for c in channels]:
            bot.send_message(ADMIN_ID, "⚠️ هذه القناة مضافة بالفعل!")
            return
        channels.append({'username': ch_username, 'link': url, 'title': ch_title})
        save_json_file(CHANNELS_FILE, channels)
        bot.send_message(ADMIN_ID, f"✅ تمت الإضافة: {ch_title}")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ فشل الجلب: {e}")

# ==================== معالجة الرسائل النصية ====================
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text.strip()

    if MAINTENANCE_MODE:
        bot.send_message(chat_id, MAINTENANCE_MESSAGE)
        return

    if not check_must_join(chat_id):
        send_join_msg(chat_id)
        return

    if chat_id in user_numbers and chat_id in pending_otp:
        if text.isdigit() and len(text) == 6:
            phone_data = user_numbers[chat_id]
            token = login_with_otp(phone_data['formatted'], text)
            
            if token:
                user_sessions[chat_id] = {
                    'phone': phone_data['formatted'],
                    'display_phone': phone_data['display'],
                    'token': token
                }
                user_numbers.pop(chat_id, None)
                pending_otp.pop(chat_id, None)
                bot.send_message(chat_id, "✅ تم تسجيل الدخول بنجاح!")
                show_main_menu(chat_id, user_sessions[chat_id]['display_phone'])
            else:
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("🔄 إعادة الإرسال", callback_data="resend_otp"),
                    types.InlineKeyboardButton("❌ إلغاء", callback_data="cancel_otp")
                )
                bot.send_message(chat_id, "❌ الرمز غير صحيح أو منتهي.", reply_markup=markup)
        else:
            bot.send_message(chat_id, "⚠️ أدخل 6 أرقام فقط.")
        return

    if text.startswith("07") and len(text) == 10 and text.isdigit():
        formatted = format_num(text)
        display_p = format_phone(text)
        user_numbers[chat_id] = {'original': text, 'formatted': formatted, 'display': display_p}
        pending_otp[chat_id] = formatted
        
        if request_otp(formatted):
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("🔄 إعادة الإرسال", callback_data="resend_otp"),
                types.InlineKeyboardButton("❌ إلغاء", callback_data="cancel_otp")
            )
            bot.send_message(chat_id, "✅ تم إرسال رمز التحقق.\nأدخل الرمز المكون من 6 أرقام:", reply_markup=markup)
        else:
            bot.send_message(chat_id, "❌ فشل إرسال الرمز.")
            user_numbers.pop(chat_id, None)
            pending_otp.pop(chat_id, None)
    else:
        bot.send_message(chat_id, "⚠️ أرسل رقم صحيح يبدأ بـ 07 ويتكون من 10 أرقام.")

# ==================== خادم Flask ====================
app = Flask(__name__)

@app.route("/")
def home():
    return "🤖 Bot is running"

def run_web():
    try:
        app.run(host="0.0.0.0", port=10000, debug=False, use_reloader=False)
    except Exception as e:
        print(f"❌ خطأ في Flask: {e}")

# ==================== تشغيل البوت ====================
def run_bot():
    restart_count = 0
    while True:
        try:
            print("="*60)
            print(f"🚀 محاولة تشغيل البوت (المرة {restart_count+1})...")
            
            # إلغاء أي webhook نشط
            try:
                bot.remove_webhook()
                print("✅ تم إلغاء الـ Webhook")
            except Exception as e:
                print(f"⚠️ فشل إلغاء webhook: {e}")
            
            print("📡 جاري الاتصال بخادم تيليجرام...")
            bot.infinity_polling(
                timeout=10, 
                long_polling_timeout=5,
                skip_pending=True
            )
            
        except KeyboardInterrupt:
            print("\n👋 تم الإيقاف يدوياً")
            sys.exit(0)
            
        except Exception as e:
            print(f"❌ خطأ في البوت: {e}")
            import traceback
            traceback.print_exc()
            print(f"⏳ إعادة التشغيل بعد 3 ثوانٍ...")
            time.sleep(3)
            restart_count += 1

# ==================== نقطة الدخول الرئيسية ====================
if __name__ == '__main__':
    print("="*60)
    print("🚀 بدء تشغيل البوت المتكامل...")
    print("="*60)
    
    # تشغيل خادم Flask في خيط منفصل
    flask_thread = Thread(target=run_web, daemon=True)
    flask_thread.start()
    print("✅ خادم Flask يعمل على المنفذ 10000")
    
    # تشغيل البوت (مع إعادة تشغيل تلقائي)
    try:
        run_bot()
    except KeyboardInterrupt:
        print("\n👋 تم الإيقاف بواسطة المستخدم")
        sys.exit(0)
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")
        sys.exit(1)
