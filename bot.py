import os
import time
import requests
from bs4 import BeautifulSoup
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# Config & Credentials
BOT_TOKEN = "8791446161:AAEP2mXMsavFFEMqcDtNkl80UpOI-d08RS4"
OWNER_ID = 8112208075
PANEL_TOKEN = "ZJ0LfnKMUEN8U1FFRA=="
BASE_URL = "http://51.75.55.16/ints/agent"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

@app.route('/')
def home():
    return "Target SMS Bot Active!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web_server)
    t.daemon = True
    t.start()

session = requests.Session()

# System State
user_balances = {}  # { client_id: earned_balance }
otp_rate = 2.0      # Default 2 PKR per OTP
processed_sms = set()
client_active_numbers = {} # { client_id: number }

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
        print(f"Fetch Ranges Error: {e}")
    
    return ["Tanzania Mic TG08", "Philippines FoodPanda", "United Kingdom"]

def fetch_numbers_for_range(selected_range):
    url = f"{BASE_URL}/MySMSNumbers"
    params = {"token": PANEL_TOKEN}
    
    # Try POST and GET for panel filtering
    data_payload = {
        "range": selected_range,
        "action": "filter",
        "submit": "Filter"
    }
    
    numbers = []
    try:
        # First attempt with POST filter
        res = session.post(url, params=params, data=data_payload, timeout=10)
        if res.status_code != 200:
            res = session.get(url, params=params, timeout=10)
            
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            rows = soup.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    range_text = cols[0].text.strip()
                    num_text = cols[1].text.strip()
                    if not num_text:
                        num_text = cols[2].text.strip()
                        
                    # Match range if selected
                    if selected_range.lower() in range_text.lower() or not selected_range:
                        if num_text.isdigit() or len(num_text) > 6:
                            numbers.append(num_text)
                            
        # Fallback parsing if table structure is raw
        if not numbers and res.status_code == 200:
            import re
            found = re.findall(r'\b\d{10,15}\b', res.text)
            if found:
                numbers = list(set(found))[:10]
    except Exception as e:
        print(f"Filter Error: {e}")
        
    return numbers

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
                    rows = soup.find_all('tr')
                    for row in rows:
                        cols = [c.text.strip() for c in row.find_all('td')]
                        if len(cols) >= 4:
                            number_in_log = cols[1]
                            sms_code = cols[3]
                            
                            log_id = f"{number_in_log}_{sms_code}"
                            if log_id not in processed_sms:
                                for client_id, assigned_num in list(client_active_numbers.items()):
                                    if assigned_num in number_in_log:
                                        processed_sms.add(log_id)
                                        user_balances[client_id] = user_balances.get(client_id, 0.0) + otp_rate
                                        bot.send_message(
                                            client_id,
                                            f"🎉 **New OTP Received!**\n\n"
                                            f"📱 **Number:** `{assigned_num}`\n"
                                            f"💬 **Code:** `{sms_code}`\n"
                                            f"💰 **Earned:** +{otp_rate} PKR"
                                        )
        except Exception as e:
            print(f"Auto OTP Error: {e}")
        time.sleep(7)

# Keyboards
def get_main_keyboard(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("🌐 Get Numbers (Select Range)"))
    markup.add(KeyboardButton("💰 My Balance"), KeyboardButton("❌ Stop Auto-OTP"))
    if user_id == OWNER_ID:
        markup.add(KeyboardButton("👑 Owner Admin Controls"))
    return markup

# Handlers
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "👋 **Welcome to Auto OTP Earning Bot!**\n\n"
        "Click below to fetch active numbers from the Target SMS panel.",
        reply_markup=get_main_keyboard(message.from_user.id)
    )

@bot.message_handler(func=lambda m: m.text == "🌐 Get Numbers (Select Range)")
def handle_get_ranges(message):
    bot.reply_to(message, "🔄 **Fetching Ranges from Panel...**")
    ranges = fetch_panel_ranges()
    
    markup = InlineKeyboardMarkup()
    for r in ranges[:8]:  # Top 8 ranges
        markup.add(InlineKeyboardButton(text=r, callback_data=f"rng_{r[:20]}"))
        
    bot.send_message(message.chat.id, "🎯 **Select Range to Get Number:**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("rng_"))
def handle_range_selection(call):
    selected_range = call.data.replace("rng_", "")
    bot.answer_callback_query(call.id, f"Selected: {selected_range}")
    
    bot.edit_message_text(
        f"⌛ **Fetching Numbers for `{selected_range}`...**",
        call.message.chat.id,
        call.message.message_id
    )
    
    numbers = fetch_numbers_for_range(selected_range)
    if numbers:
        num = numbers[0]
        client_active_numbers[call.from_user.id] = num
        
        bot.send_message(
            call.message.chat.id,
            f"✅ **Number Successfully Assigned!**\n\n"
            f"📱 **Your Number:** `{num}`\n"
            f"🎯 **Range:** {selected_range}\n\n"
            f"⚡ **Auto OTP Detection is ACTIVE.**",
            reply_markup=get_main_keyboard(call.from_user.id)
        )
    else:
        bot.send_message(
            call.message.chat.id,
            "⚠️ **No active number available for this range currently.**\n"
            "Please try selecting another range."
        )

@bot.message_handler(func=lambda m: m.text == "💰 My Balance")
def handle_balance(message):
    uid = message.from_user.id
    bal = user_balances.get(uid, 0.0)
    bot.reply_to(
        message,
        f"💳 **Your Total Earned Balance:**\n\n"
        f"💵 **Balance:** `{bal}` PKR\n"
        f"🏷️ **Current Rate:** `{otp_rate}` PKR / OTP\n"
        f"🆔 **Your User ID:** `{uid}`"
    )

@bot.message_handler(func=lambda m: m.text == "❌ Stop Auto-OTP")
def handle_stop(message):
    uid = message.from_user.id
    if uid in client_active_numbers:
        del client_active_numbers[uid]
        bot.reply_to(message, "🛑 **Auto-OTP monitoring stopped.**")
    else:
        bot.reply_to(message, "ℹ️ **No active number found to stop.**")

# Owner Controls
@bot.message_handler(func=lambda m: m.text == "👑 Owner Admin Controls")
def handle_owner_panel(message):
    if message.from_user.id != OWNER_ID:
        return
    bot.reply_to(
        message,
        f"👑 **Owner Control Panel**\n\n"
        f"• Current OTP Rate: {otp_rate} PKR\n"
        f"• Active Clients: {len(client_active_numbers)}\n\n"
        "To set rate, send: `/setrate 2.5`"
    )

@bot.message_handler(commands=['setrate'])
def set_rate(message):
    global otp_rate
    if message.from_user.id == OWNER_ID:
        try:
            val = float(message.text.split()[1])
            otp_rate = val
            bot.reply_to(message, f"✅ **OTP Rate updated to {otp_rate} PKR.**")
        except:
            bot.reply_to(message, "Usage: `/setrate 2.5`")

if __name__ == '__main__':
    keep_alive()
    Thread(target=auto_otp_checker, daemon=True).start()
    bot.infinity_polling(skip_pending=True)

