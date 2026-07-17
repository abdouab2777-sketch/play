import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# التوكن ممتد الصلاحية لـ 60 يوماً الذي استخرجناه سوياً
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "EAAXmzOXloWcBR3oY3nA5Kcu1YAtF9vZCqOZA4pEyIitXFLKDA5haz1tDVZAzTKO5ZAr1oXEuLVZC1MXT5ZA53lO6XC9R9TrB3zSNEYcQklgH2tWmUrUZAZACE7uQ1Fd5FK6nSSGeT7twfLyykMh6pZBAholAQvKhoD5ELSXChHmMPLX2lPb6JCZBE4WeZCGsaNaXiI1")

# رمز التحقق الذي ستكتبه في مطوري فيسبوك (يمكنك تعديله كما تشاء)
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "yakoub123")


def send_messenger_message(recipient_id, text_reply):
    """إرسال الرد التلقائي عبر الـ Send API الخاص بفيسبوك"""
    url = f"https://graph.facebook.com/v16.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text_reply}
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"✅ تم إرسال الرد بنجاح إلى الـ ID: {recipient_id}")
        else:
            print(f"❌ خطأ إرسال من فيسبوك: {response.json()}")
    except Exception as e:
        print(f"❌ فشل الاتصال بخوادم فيسبوك: {e}")


@app.route('/', methods=['GET'])
def index():
    return "🚀 سيرفر بوت بايثون يعمل بنجاح ومستعد لاستقبال الرسائل!"


@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # --- 1. عملية التحقق من الويب هوك (GET) ---
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if mode and token:
            if mode == 'subscribe' and token == VERIFY_TOKEN:
                print("✅ تم التحقق بنجاح من الويب هوك بواسطة فيسبوك!")
                return challenge, 200
            else:
                print("❌ فشل التحقق: رمز التحقق غير متطابق.")
                return "Forbidden", 403
        return "Missing parameters", 400

    # --- 2. استقبال الرسائل والرد الفوري عليها (POST) ---
    if request.method == 'POST':
        data = request.json
        
        if data.get('object') == 'page':
            for entry in data.get('entry', []):
                for messaging_event in entry.get('messaging', []):
                    
                    # قراءة الرسائل الواردة فقط وتجاهل الرسائل الصادرة من البوت نفسه (is_echo)
                    if messaging_event.get('message') and not messaging_event.get('message', {}).get('is_echo'):
                        sender_id = messaging_event['sender']['id'] # الـ PSID الخاص بالمستخدم للرد عليه
                        message_text = messaging_event['message'].get('text', '').strip()
                        
                        print(f"📥 رسالة جديدة من {sender_id}: {message_text}")
                        
                        # --- منطق الردود التلقائية ---
                        user_msg = message_text.lower()
                        reply_text = ""
                        
                        if user_msg in ["مرحبا", "هلا", "hi", "hello", "السلام عليكم"]:
                            reply_text = "أهلاً بك يا غالي! كيف يمكنني مساعدتك اليوم؟ 😊"
                        elif "سؤال جاهز" in user_msg:
                            reply_text = "تم استقبال سؤالك الجاهز بنجاح! جاري التجهيز والرد عليك فوراً يا بطل."
                        elif "البوت" in user_msg:
                            reply_text = "أنا بوت ذكي ومستقر مبرمج بالكامل بلغة بايثون ومستضاف على خادم سحابي! 🐍"
                        else:
                            # رد افتراضي لأي رسالة أخرى
                            reply_text = f"أهلاً بك، لقد استلمت رسالتك: '{message_text}' وجاري مراجعتها."
                        
                        # إرسال الرد الفوري
                        if reply_text:
                            send_messenger_message(sender_id, reply_text)
                            
            return "EVENT_RECEIVED", 200
        else:
            return "Not Found", 404

if __name__ == '__main__':
    # تحديد المنفذ تلقائياً ليتوافق مع منصات الاستضافة الخارجية مثل Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
