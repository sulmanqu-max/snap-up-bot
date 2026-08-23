import os
import time
import requests
from bs4 import BeautifulSoup
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# Config & Credentials
BOT_TOKEN = "8215360361:AAFzEOumwGJ0p1jHsMa--GWsJtrMQ2__IXw"
OWNER_ID = 8112208075
PANEL_TOKEN = "ZJOLfnKMUEM8U1FFRA=="
BASE_URL = "http://51.75.55.16/ints/agent"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

@app.route('/')
def home():
    return "Earned Balance & Reset Bot Active!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web_server)
    t.daemon = True
    t.start()

session = requests.Session()

# System State
user_balances = {}          # { client_id: earned_balance }
otp_rate = 2.0              # Default 2 PKR per OTP
processed_sms = set()
client_active_numbers = {}  # { client_id: number }

# Panel Functions
def fetch_panel_ranges():
    url = f"{BASE_URL}/MySMSNumbers"
    params = {"token": PANEL_TOKEN}
    try:
        res = session.get(url, params=params, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            select_box = soup.find('select', {'name': 'range'}) or soup.find('select')
            if select_box:
                options = select_box.find_all('option')
                ranges = [opt.text.strip() for opt in options if opt.text.strip()]
                if ranges:
                    return ranges
    except Exception as e:
        print(f"[Fetch Ranges Error]: {e}")
    return ["Philippines Foodpanda", "Tanzania Mic TG08"]

def fetch_numbers_for_range(selected_range):
    url = f"{BASE_URL}/MySMSNumbers"
    params = {"token": PANEL_TOKEN}
    payload = {"range": selected_range, "action": "filter", "submit": "Filter"}
    try:
        res = session.post(url, params=params, data=payload, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            rows = soup.find_all('tr')
            numbers = []
            for row in rows[1:10]:
                cols = [c.text.strip() for c in row.find_all('td')]
                if len(cols) >= 3:
                    numbers.append(cols[2])
            return numbers
    except Exception as e:
        print(f"[Filter Error]: {e}")
    return []

# Background Worker for Auto-Adding Balance per OTP
def auto_otp_checker():
    global user_balances
    print("Auto OTP Earning Worker started...")
    while True:
        try:
            if client_active_numbers:
                url = f"{BASE_URL}/SMSCDRStats"
                params = {"token": PANEL_TOKEN}
                res = session.get(url, params=params, timeout=10)
                
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, 'html.parser')
                    table = soup.find('table')
                    if table:
                        rows = table.find_all('tr')
                        for row in rows[1:10]:
                            cols = [c.text.strip() for c in row.find_all('td')]
                            if len(cols) >= 5:
                                date = cols[0]
                                panel_num = cols[2]
                                cli = cols[3]
                                sms_text = cols[4]
                                
                                sms_sig = f"{date}_{panel_num}_{sms_text}"
                                if sms_sig not in processed_sms:
                                    for client_id, target_num in list(client_active_numbers.items()):
                                        if target_num in panel_num or panel_num in target_num:
                                            cid = int(client_id)
                                            
                                            # ADD PER OTP RATE TO CLIENT BALANCE
                                            old_bal = user_balances.get(cid, 0.0)
                                            new_bal = round(old_bal + otp_rate, 2)
                                            user_balances[cid] = new_bal
                                            
                                            msg = (
                                                f"🚨 **New OTP Received!**\n\n"
                                                f"📞 **Number:** `{panel_num}`\n"
                                                f"🏷️ **Service:** {cli}\n"
                                                f"💬 **OTP Code:** `{sms_text}`\n"
                                                f"⏱️ **Time:** {date}\n\n"
                                                f"➕ **Earned:** +{otp_rate} PKR\n"
                                                f"💰 **Total Balance:** {new_bal} PKR"
                                            )
                                            try:
                                                bot.send_message(cid, msg, parse_mode="Markdown")
                                            except Exception as err:
                                                print(f"Error sending msg: {err}")
                                            
                                            processed_sms.add(sms_sig)
        except Exception as e:
            print(f"[Worker Error]: {e}")
        time.sleep(10)

def start_worker():
    t = Thread(target=auto_otp_checker)
    t.daemon = True
    t.start()

# Telegram Handlers
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    if user_id not in user_balances:
        user_balances[user_id] = 0.0
        
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("🌐 Get Numbers (Select Range)"))
    markup.row(KeyboardButton("💰 My Balance"), KeyboardButton("❌ Stop Auto-OTP"))
    
    if user_id == OWNER_ID:
        markup.row(KeyboardButton("👑 Owner Admin Controls"))

    bot.send_message(
        message.chat.id,
        f"👋 **Welcome to SMS Earning Bot!**\n\n"
        f"🏷️ **Rate per OTP:** {otp_rate} PKR\n"
        f"💳 **Your Current Balance:** {user_balances[user_id]} PKR\n\n"
        "نیچے دیے گئے مینو سے اپشن سلیکٹ کریں:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text == "💰 My Balance")
def check_balance(message):
    user_id = message.from_user.id
    bal = user_balances.get(user_id, 0.0)
    bot.reply_to(
        message, 
        f"💳 **Your Total Earned Balance:**\n\n"
        f"💵 **Balance:** `{bal}` PKR\n"
        f"🏷️ **Current Rate:** `{otp_rate}` PKR / OTP\n"
        f"🆔 **Your User ID:** `{user_id}`",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text == "🌐 Get Numbers (Select Range)")
def show_ranges(message):
    bot.reply_to(message, "🔄 پینل سے رینجز فیچ کی جا رہی ہیں...")
    ranges = fetch_panel_ranges()
    inline_kbd = InlineKeyboardMarkup()
    for r in ranges:
        inline_kbd.add(InlineKeyboardButton(text=f"📂 {r}", callback_data=f"rng_{r[:25]}"))
    
    bot.send_message(message.chat.id, "👇 رینج منتخب کریں:", reply_markup=inline_kbd)

@bot.callback_query_handler(func=lambda call: call.data.startswith('rng_'))
def handle_range(call):
    selected_range = call.data.replace("rng_", "")
    bot.answer_callback_query(call.id, "Loading numbers...")
    bot.edit_message_text(f"⏳ `{selected_range}` کے نمبرز نکالے جا رہے ہیں...", call.message.chat.id, call.message.message_id)
    
    numbers = fetch_numbers_for_range(selected_range)
    if numbers:
        num_buttons = InlineKeyboardMarkup()
        for num in numbers:
            num_buttons.add(InlineKeyboardButton(text=f"📱 {num}", callback_data=f"selnum_{num}"))
        bot.send_message(call.message.chat.id, "✅ **نمبر پر کلک کر کے لاک کریں:**", reply_markup=num_buttons)
    else:
        bot.send_message(call.message.chat.id, "⚠️ فی الحال کوئی ایکٹیو نمبر دستیاب نہیں ہے۔")

@bot.callback_query_handler(func=lambda call: call.data.startswith('selnum_'))
def handle_number_select(call):
    selected_num = call.data.replace("selnum_", "")
    client_id = str(call.from_user.id)
    client_active_numbers[client_id] = selected_num
    
    bot.answer_callback_query(call.id, "Number Locked!")
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"✅ **Number Locked:** `{selected_num}`\n\n"
             f"جیسے ہی OTP آئے گا، `{otp_rate}` PKR آپ کے بیلنس میں جمع کر دیے جائیں گے!",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text == "❌ Stop Auto-OTP")
def stop_otp(message):
    client_id = str(message.from_user.id)
    if client_id in client_active_numbers:
        del client_active_numbers[client_id]
        bot.reply_to(message, "🛑 نمبر ان لاک کر دیا گیا ہے۔")
    else:
        bot.reply_to(message, "⚠️ کوئی نمبر لاک نہیں تھا۔")

# Owner Admin Controls
@bot.message_handler(func=lambda m: m.text == "👑 Owner Admin Controls")
def owner_panel(message):
    if message.from_user.id != OWNER_ID:
        return
    bot.reply_to(
        message,
        f"👑 **Owner Controls & Commands:**\n\n"
        f"1️⃣ **پر OTP ریٹ سیٹ کریں:**\n`/setrate 2` (یا جتنے PKR رکھنے ہوں)\n\n"
        f"2️⃣ **کسی ایک کلائنٹ کا بیلنس ڈیلیٹ/زیرو کریں:**\n`/resetuser USER_ID`\n*(مثلاً: `/resetuser 12345678`)*\n\n"
        f"3️⃣ **تمام کلائنٹس کا بیلنس ڈیلیٹ کریں (New Week Reset):**\n`/resetall`\n\n"
        f"📊 **Current Status:**\n"
        f"• Rate per OTP: {otp_rate} PKR\n"
        f"• Active Users Recorded: {len(user_balances)}",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['setrate'])
def set_rate_cmd(message):
    global otp_rate
    if message.from_user.id != OWNER_ID:
        return
    try:
        new_rate = float(message.text.split()[1])
        otp_rate = new_rate
        bot.reply_to(message, f"✅ **Per OTP Earning Rate updated to:** `{otp_rate}` PKR", parse_mode="Markdown")
    except Exception:
        bot.reply_to(message, "⚠️ صحیح طریقہ: `/setrate 2`", parse_mode="Markdown")

@bot.message_handler(commands=['resetuser'])
def reset_single_user(message):
    if message.from_user.id != OWNER_ID:
        return
    try:
        target_id = int(message.text.split()[1])
        user_balances[target_id] = 0.0
        bot.reply_to(message, f"🧹 User `{target_id}` کا بیلنس 0 PKR کر دیا گیا ہے۔", parse_mode="Markdown")
        try:
            bot.send_message(target_id, "🔄 آپ کا پچھلا بیلنس کلیئر کر دیا گیا ہے۔ نیا ہفتہ زِیرو بیلنس سے شروع ہو گیا ہے!", parse_mode="Markdown")
        except Exception:
            pass
    except Exception:
        bot.reply_to(message, "⚠️ صحیح طریقہ: `/resetuser 123456789`", parse_mode="Markdown")

@bot.message_handler(commands=['resetall'])
def reset_all_users(message):
    global user_balances
    if message.from_user.id != OWNER_ID:
        return
    for uid in list(user_balances.keys()):
        user_balances[uid] = 0.0
        try:
            bot.send_message(uid, "🎉 **Weekly Reset!**\n\nتمام کلائنٹس کا پچھلا بیلنس کلیئر کر دیا گیا ہے۔ نیا ہفتہ شروع ہو گیا ہے!", parse_mode="Markdown")
        except Exception:
            pass
    bot.reply_to(message, "✅ **تمام کلائنٹس کا بیلنس کامیابی سے 0 (زیرو) کر دیا گیا ہے۔**")

# Main Loop
def main():
    keep_alive()
    start_worker()
    print("Earning & Reset Bot active...")
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=60)
        except Exception as e:
            print(f"[Polling Error]: {e}")
            time.sleep(3)

if __name__ == '__main__':
    main()


            
