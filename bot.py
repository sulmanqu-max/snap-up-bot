from threading import Thread
from flask import Flask
import os
import re
import time
import requests
from bs4 import BeautifulSoup
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

app = Flask('')

@app.route('/')
def home():
    return 'Bot is alive!'

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

# ---------------- CONFIGURATION ----------------
BOT_TOKEN = "8922159939:AAHcnokuJl-EhO5mprlZcknm3tpwQ1b9gqM"
bot = telebot.TeleBot(BOT_TOKEN)

ADMIN_ID = 8112208075

PANEL_BASE_URL = "http://51.75.55.16/ints"
API_TOKEN = "ZJOLfnKMUEM8U1FFRA=="

MY_NUMBERS_URL = f"{PANEL_BASE_URL}/agent/MySMSNumbers"
SMS_LOGS_URL = f"{PANEL_BASE_URL}/agent/SmsLogs"

NUMBERS_FILE = "numbers.txt"

COUNTRIES = {
    "PK": {"name": "🇵🇰 Pakistan", "code": "+92"},
    "IN": {"name": "🇮🇳 India", "code": "+91"},
    "US": {"name": "🇺🇸 USA", "code": "+1"},
    "UK": {"name": "🇬🇧 UK", "code": "+44"},
    "BD": {"name": "🇧🇩 Bangladesh", "code": "+880"},
    "AE": {"name": "🇦🇪 UAE", "code": "+971"},
    "SA": {"name": "🇸🇦 Saudi Arabia", "code": "+966"},
    "CA": {"name": "🇨🇦 Canada", "code": "+1"},
    "DE": {"name": "🇩🇪 Germany", "code": "+49"},
    "FR": {"name": "🇫🇷 France", "code": "+33"},
    "RU": {"name": "🇷🇺 Russia", "code": "+7"},
    "CN": {"name": "🇨🇳 China", "code": "+86"},
    "BR": {"name": "🇧🇷 Brazil", "code": "+55"},
    "ID": {"name": "🇮🇩 Indonesia", "code": "+62"},
    "TR": {"name": "🇹🇷 Turkey", "code": "+90"},
    "EG": {"name": "🇪🇬 Egypt", "code": "+20"},
    "NG": {"name": "🇳🇬 Nigeria", "code": "+234"},
    "ZA": {"name": "🇿🇦 South Africa", "code": "+27"},
    "MY": {"name": "🇲🇾 Malaysia", "code": "+60"},
    "PH": {"name": "🇵🇭 Philippines", "code": "+63"},
    "VN": {"name": "🇻🇳 Vietnam", "code": "+84"},
    "TH": {"name": "🇹🇭 Thailand", "code": "+66"},
    "KW": {"name": "🇰🇼 Kuwait", "code": "+965"},
    "QA": {"name": "🇶🇦 Qatar", "code": "+974"},
    "OM": {"name": "🇴🇲 Oman", "code": "+968"},
    "BH": {"name": "🇧🇭 Bahrain", "code": "+973"},
    "AF": {"name": "🇦🇫 Afghanistan", "code": "+93"},
    "IR": {"name": "🇮🇷 Iran", "code": "+98"},
    "IQ": {"name": "🇮🇶 Iraq", "code": "+964"}
}

def load_saved_numbers():
    if os.path.exists(NUMBERS_FILE):
        with open(NUMBERS_FILE, "r") as f:
            return [line.strip() for line in f if line.strip()]
    return []

def save_numbers_to_file(numbers):
    with open(NUMBERS_FILE, "w") as f:
        for num in numbers:
            f.write(f"{num}\n")

ADDED_NUMBERS_LIST = load_saved_numbers()
USERS_DB = {}
SETTINGS = {"otp_price": 2.0}

def get_api_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Authorization": f"Bearer {API_TOKEN}",
        "token": API_TOKEN
    })
    return session

def fetch_panel_numbers_api():
    session = get_api_session()
    try:
        res = session.get(MY_NUMBERS_URL, params={"token": API_TOKEN}, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        extracted_numbers = []

        tables = soup.find_all("table")
        for table in tables:
            for tr in table.find_all("tr"):
                tds = tr.find_all("td")
                if tds:
                    for td in tds:
                        text = td.get_text(strip=True)
                        nums = re.findall(r"\b\d{8,15}\b", text)
                        for n in nums:
                            formatted_num = f"+{n}" if not n.startswith("+") else n
                            extracted_numbers.append(formatted_num)

        return list(set(extracted_numbers))
    except Exception as e:
        print(f"Error fetching numbers: {e}")
        return []

def fetch_otp_logs_api():
    session = get_api_session()
    try:
        res = session.get(SMS_LOGS_URL, params={"token": API_TOKEN}, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        otps = []

        for tr in soup.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) >= 2:
                raw_text = [td.get_text(strip=True) for td in tds]
                number = raw_text[0] if len(raw_text) > 0 else ""
                message = raw_text[1] if len(raw_text) > 1 else ""

                otp_code = re.findall(r"\b\d{4,8}\b", message)
                extracted_otp = otp_code[0] if otp_code else "Code Not Extracted"

                if message and number:
                    otps.append({
                        "number": number,
                        "message": message,
                        "otp": extracted_otp
                    })

        return otps
    except Exception as e:
        print(f"Error fetching OTP: {e}")
        return []

def owner_keyboard():
    markup = ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    markup.add(KeyboardButton("➕ Add Numbers"), KeyboardButton("📋 Added List"), KeyboardButton("📱 My Numbers"))
    markup.add(KeyboardButton("🔄 Fetch Panel Numbers"), KeyboardButton("⚙️ Set Rate"), KeyboardButton("💳 My Balance"))
    markup.add(KeyboardButton("📊 All Users"), KeyboardButton("📥 Check OTP"), KeyboardButton("🗑️ Delete All"))
    markup.add(KeyboardButton("👤 Switch to Client Board"))
    return markup

def client_keyboard(is_owner=False):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(KeyboardButton("📱 My Numbers"), KeyboardButton("📥 Check OTP"))
    markup.add(KeyboardButton("💳 My Balance"))
    if is_owner:
        markup.add(KeyboardButton("👑 Switch to Owner Board"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user = message.from_user
    user_id = user.id
    username = f"@{user.username}" if user.username else "No Username"
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()

    if user_id not in USERS_DB:
        USERS_DB[user_id] = {"name": full_name, "username": username, "balance": 0.0}

    if user_id == ADMIN_ID:
        bot.send_message(message.chat.id, "👑 **Welcome Owner! Target SMS Panel Linked.**", reply_markup=owner_keyboard(), parse_mode="Markdown")
    else:
        bot.send_message(
            message.chat.id,
            f"👋 **Welcome {full_name}!**\n\n💰 **Balance:** `{USERS_DB[user_id]['balance']} PKR`",
            reply_markup=client_keyboard(),
            parse_mode="Markdown"
        )

@bot.message_handler(func=lambda msg: msg.text == "🔄 Fetch Panel Numbers")
def handle_fetch_panel_numbers(message):
    if message.from_user.id != ADMIN_ID: return
    bot.reply_to(message, "🔐 Fetching panel numbers...")
    
    panel_nums = fetch_panel_numbers_api()
    if panel_nums:
        added_count = 0
        for num in panel_nums:
            if num not in ADDED_NUMBERS_LIST:
                ADDED_NUMBERS_LIST.append(num)
                added_count += 1
        
        save_numbers_to_file(ADDED_NUMBERS_LIST)
        bot.reply_to(
            message,
            f"✅ **{added_count}** new panel numbers loaded!\n📋 Total Stored Numbers: `{len(ADDED_NUMBERS_LIST)}`",
            parse_mode="Markdown"
        )
    else:
        bot.reply_to(message, "⚠️ No numbers found in panel.")

@bot.message_handler(func=lambda msg: msg.text in ["📱 My Numbers", "/mynumbers"])
def show_available_countries(message):
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = []
    
    for key, data in COUNTRIES.items():
        code = data['code']
        has_numbers = any(num.startswith(code) for num in ADDED_NUMBERS_LIST)
        if has_numbers:
            buttons.append(InlineKeyboardButton(f"{data['name']} ({code})", callback_data=f"get_country_ranges_{key}"))

    if buttons:
        markup.add(*buttons)
        bot.reply_to(message, "🌍 **Select Country (Active Panel Numbers Available):**", reply_markup=markup, parse_mode="Markdown")
    else:
        bot.reply_to(message, "⚠️ Currently no panel numbers available. Click **🔄 Fetch Panel Numbers** to sync panel data.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("get_country_ranges_"))
def display_country_ranges(call):
    country_key = call.data.split("_")[-1]
    country_info = COUNTRIES.get(country_key)
    code = country_info["code"]

    country_numbers = [n for n in ADDED_NUMBERS_LIST if n.startswith(code)]
    ranges = list(set([num[:6] for num in country_numbers]))

    markup = InlineKeyboardMarkup(row_width=2)
    buttons = [InlineKeyboardButton(f"Range {r}...", callback_data=f"show_range_nums_{country_key}_{r}") for r in ranges]
    markup.add(*buttons)
    markup.add(InlineKeyboardButton("🔙 Back to Countries", callback_data="back_to_countries"))

    bot.answer_callback_query(call.id, f"Ranges for {country_info['name']}")
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"🎯 **{country_info['name']} Available Ranges:**\nSelect a range to view numbers:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("show_range_nums_"))
def display_range_numbers(call):
    parts = call.data.split("_")
    country_key = parts[3]
    selected_range = parts[4]

    range_numbers = [num for num in ADDED_NUMBERS_LIST if num.startswith(selected_range)]
    formatted = "\n".join([f"{i+1}. `{num}`" for i, num in enumerate(range_numbers[:10])])

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Back to Ranges", callback_data=f"get_country_ranges_{country_key}"))

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"📱 **Numbers in Range `{selected_range}`:**\n\n{formatted}",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "back_to_countries")
def back_to_countries_menu(call):
    show_available_countries(call.message)

@bot.message_handler(func=lambda msg: msg.text == "📥 Check OTP")
def handle_check_otp(message):
    user_id = message.from_user.id
    bot.reply_to(message, "🔍 Checking live OTP from Target SMS Panel...")
    
    otps = fetch_otp_logs_api()
    if otps:
        formatted_list = []
        for item in otps[:5]:
            formatted_list.append(
                f"📱 **Number:** `{item['number']}`\n"
                f"💬 **Full Message:** `{item['message']}`\n"
                f"🔑 **Extracted Code:** `{item['otp']}`"
            )
        
        response_msg = "📥 **Received OTP Logs:**\n\n" + "\n\n---\n\n".join(formatted_list)
        bot.reply_to(message, response_msg, parse_mode="Markdown")
    else:
        bot.reply_to(message, "ℹ️ No OTP received yet in panel.")

@bot.message_handler(func=lambda msg: msg.text == "💳 My Balance")
def check_balance(message):
    user_id = message.from_user.id
    bal = USERS_DB.get(user_id, {}).get("balance", 0.0)
    bot.reply_to(message, f"💳 **Your Balance:** `{bal} PKR`", parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "👤 Switch to Client Board")
def switch_to_client_board(message):
    if message.from_user.id != ADMIN_ID: return
    bot.send_message(message.chat.id, "🔄 Switched to Client Board!", reply_markup=client_keyboard(is_owner=True))

@bot.message_handler(func=lambda msg: msg.text == "👑 Switch to Owner Board")
def switch_to_owner_board(message):
    if message.from_user.id != ADMIN_ID: return
    bot.send_message(message.chat.id, "👑 Switched to Owner Board!", reply_markup=owner_keyboard())

print("Bot running...")
while True:
    try:
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        time.sleep(5)
                      
