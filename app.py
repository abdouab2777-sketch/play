import os
import requests
from flask import Flask, request

app = Flask(__name__)

# --- الإعدادات الصحيحة والنهائية لصفحة Google play point ---
PAGE_ACCESS_TOKEN = "EAAXmzOXloWcBRzSNXpcmen2bWOnhZC4hs9JF2z0tJVKgaaVZAvsTRerB9ZAnqfZAG5AfG0UKHKPVWf0kfxzNdaXEQfaGXwuhLEPs34KuYR6YigQZBFzLq1RMo9qWdxAuzEXD3xtxu5BqPjISA78a8tRKu283g0IBFCZAnqcJIZAgzVZBegyMDt4GYAbFrf7lqqlocozqemLK"
PAGE_ID = "1250641121458104" 
VERIFY_TOKEN = "yakoub123"

def send_messenger_message(recipient_id, text_reply):
    """إرسال الرد التلقائي باستخدام معرف الصفحة المباشر لتفادي أخطاء الصلاحيات"""
    url = f"https://graph.facebook.com/v16.0/{PAGE_ID}/messages?access_token={PAGE_ACCESS_TOKEN}"
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
    return "🚀 البوت يعمل الآن وبكل كفاءة لصفحة Google Play Point!"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # 1. التحقق من الويب هوك (GET)
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Forbidden", 403

    # 2. استقبال الرسائل والرد (POST)
    if request.method == 'POST':
        data = request.json
        if data and data.get('object') == 'page':
            for entry in data.get('entry', []):
                for messaging_event in entry.get('messaging', []):
                    # نتحقق أن الرسالة ليست مرسلة من البوت نفسه
                    if messaging_event.get('message') and not messaging_event.get('message', {}).get('is_echo'):
                        sender_id = messaging_event['sender']['id']
                        message_text = messaging_event['message'].get('text', '').strip()
                        
                        print(f"📥 رسالة جديدة من {sender_id}: {message_text}")
                        
                        # منطق الردود
                        user_msg = message_text.lower()
                        reply = ""
                        
                        if any(word in user_msg for word in ["مرحبا", "هلا", "hi", "السلام"]):
                            reply = "أهلاً بك في صفحة Google Play Point! كيف يمكنني مساعدتك اليوم؟ 😊"
                        elif "البوت" in user_msg:
                            reply = "أنا بوت ذكي يعمل بنظام بايثون لخدمة زوار الصفحة 24/7! 🚀"
                        elif "سؤال جاهز" in user_msg:
                            reply = "جاري معالجة سؤالك يا بطل، لحظات وأرد عليك!"
                        else:
                            reply = f"أهلاً بك، استلمت رسالتك: '{message_text}' وسأرد عليك قريباً!"
                        
                        send_messenger_message(sender_id, reply)
                            
            return "EVENT_RECEIVED", 200
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
