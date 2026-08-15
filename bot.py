from threading import Thread
from flask import Flask

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
import os
import re
import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8922159939:AAHcnokuJl-EhO5mprlZcknm3tpwQ1b9gqM"
bot = telebot.TeleBot(BOT_TOKEN)

ADMIN_ID = 8112208075

LOGIN_URL = "http://51.75.55.16/ints/login"
MY_NUMBERS_URL = "http://51.75.55.16/ints/agent/MySMSNumbers"
SMS_LOGS_URL = "http://51.75.55.16/ints/agent/SmsLogs"

USERNAME = "Sulman12"
PASSWORD = "Sulman12"

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

def get_authenticated_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": LOGIN_URL,
        "Origin": "http://51.75.55.16"
    })
    try:
        res = session.get(LOGIN_URL, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        form = soup.find("form")
        action_path = form.get("action") if form else ""
        action_url = urljoin(LOGIN_URL, action_path) if action_path else LOGIN_URL

        # Auto Math Captcha Solver
        answer = None
        match = re.search(r"(\d+)\s*([\+\-\*])\s*(\d+)", res.text)
        if match:
            n1, op, n2 = int(match.group(1)), match.group(2), int(match.group(3))
            if op == '+': answer = str(n1 + n2)
            elif op == '-': answer = str(n1 - n2)
            elif op == '*': answer = str(n1 * n2)

        payload = {}
        if form:
            for inp in form.find_all("input"):
                name = inp.get("name")
                if name:
                    payload[name] = inp.get("value", "")

        if form:
            for inp in form.find_all("input"):
                inp_name = inp.get("name", "").lower()
                if any(term in inp_name for term in ["user", "email", "login", "identity"]):
                    payload[inp.get("name")] = USERNAME
                elif any(term in inp_name for term in ["pass", "pwd"]):
                    payload[inp.get("name")] = PASSWORD

        payload["username"] = USERNAME
        payload["email"] = USERNAME
        payload["password"] = PASSWORD

        if answer:
            payload["captcha"] = answer
            payload["captcha_answer"] = answer
            payload["code"] = answer
            payload["answer"] = answer
            
            if form:
                for inp in form.find_all("input"):
                    inp_name = inp.get("name", "").lower()
                    if any(c_term in inp_name for c_term in ["capt", "code", "ans", "num", "res"]):
                        payload[inp.get("name")] = answer

        payload["login"] = "LOGIN"
        payload["submit"] = "Submit"

        login_res = session.post(action_url, data=payload, allow_redirects=True, timeout=10)
        
        check_dash = session.get(MY_NUMBERS_URL, timeout=10)
        if "login" in check_dash.url.lower():
            return None, f"Login Failed (Captcha Answer: {answer})"

        return session, None
    except Exception as e:
        return None, str(e)

# ---------------- SCRAPE MY SMS NUMBERS PAGE ----------------
def fetch_panel_numbers(session):
    try:
        res = session.get(MY_NUMBERS_URL, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        extracted_numbers = []

        # Find table and extract numbers from tds
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
        print(f"Error fetching panel numbers: {e}")
        return []

def fetch_otp_logs(session):
    try:
        res = session.get(SMS_LOGS_URL, timeout=10)
        if "login" in res.url.lower() and "agent" not in res.url.lower():
            return []

        soup = BeautifulSoup(res.text, "html.parser")
        otps = []

        for tr in soup.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) >= 2:
                raw_text = [td.get_text(strip=True) for td in tds]
                number = raw_text[0] if len(raw_text) > 0 else ""
                message = raw_text[1] if len(raw_text) > 1 else ""

                otp_code = re.findall(r"\b\d{4,6}\b", message)
                extracted_otp = otp_code[0] if otp_code else "No Code Found"

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
        bot.send_message(message.chat.id, "👑 **Welcome Owner!**", reply_markup=owner_keyboard(), parse_mode="Markdown")
    else:
        bot.send_message(
            message.chat.id,
            f"👋 **Welcome {full_name}!**\n\n💰 **Balance:** `{USERS_DB[user_id]['balance']} PKR`",
            reply_markup=client_keyboard(),
            parse_mode="Markdown"
        )

# ---------------- FETCH NUMBERS BUTTON ----------------
@bot.message_handler(func=lambda msg: msg.text == "🔄 Fetch Panel Numbers")
def handle_fetch_panel_numbers(message):
    if message.from_user.id != ADMIN_ID: return
    bot.reply_to(message, "🔐 Logging into panel and fetching numbers from My SMS Numbers page...")
    
    session, err = get_authenticated_session()
    if session:
        panel_nums = fetch_panel_numbers(session)
        if panel_nums:
            added_count = 0
            for num in panel_nums:
                if num not in ADDED_NUMBERS_LIST:
                    ADDED_NUMBERS_LIST.append(num)
                    added_count += 1
            
            save_numbers_to_file(ADDED_NUMBERS_LIST)
            bot.reply_to(
                message,
                f"✅ **{added_count}** naye numbers **My SMS Numbers** پیج سے میموری میں سیو ہو گئے!\n📋 Total Stored Numbers: `{len(ADDED_NUMBERS_LIST)}`",
                parse_mode="Markdown"
            )
        else:
            bot.reply_to(message, "⚠️ My SMS Numbers page par koi number nahi mila.")
    else:
        bot.reply_to(message, f"❌ Panel Login Error: {err}")

@bot.message_handler(func=lambda msg: msg.text == "⚙️ Set Rate")
def set_rate_start(message):
    if message.from_user.id != ADMIN_ID: return
    msg = bot.reply_to(message, f"⚙️ **Current Rate:** `{SETTINGS['otp_price']} PKR` per OTP\n\nNaya rate likhein:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_set_rate)

def process_set_rate(message):
    try:
        new_rate = float(message.text.strip())
        SETTINGS["otp_price"] = new_rate
        bot.reply_to(message, f"✅ **OTP Rate updated to:** `{new_rate} PKR`", parse_mode="Markdown")
    except ValueError:
        bot.reply_to(message, "❌ Invalid numeric value.")

@bot.message_handler(func=lambda msg: msg.text == "💳 My Balance")
def check_balance(message):
    user_id = message.from_user.id
    if user_id not in USERS_DB:
        user = message.from_user
        username = f"@{user.username}" if user.username else "No Username"
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        USERS_DB[user_id] = {"name": full_name, "username": username, "balance": 0.0}

    bal = USERS_DB[user_id].get("balance", 0.0)
    bot.reply_to(message, f"💳 **Your Balance:** `{bal} PKR`", parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "➕ Add Numbers")
def add_numbers_start(message):
    if message.from_user.id != ADMIN_ID: return
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = [InlineKeyboardButton(f"{data['name']} ({data['code']})", callback_data=f"add_country_{key}") for key, data in COUNTRIES.items()]
    markup.add(*buttons)
    bot.reply_to(message, "🌍 **Select Country:**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("add_country_"))
def ask_numbers_for_country(call):
    if call.from_user.id != ADMIN_ID: return
    country_key = call.data.split("_")[-1]
    country_info = COUNTRIES.get(country_key)
    msg = bot.send_message(
        call.message.chat.id,
        f"📝 Send numbers for **{country_info['name']} ({country_info['code']})**:",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, process_save_country_numbers, country_info)

def process_save_country_numbers(message, country_info):
    raw_text = message.text.strip()
    extracted_nums = re.findall(r"\b\d{7,15}\b", raw_text)
    code = country_info["code"]
    
    if extracted_nums:
        added_count = 0
        for num in extracted_nums:
            if not num.startswith(code.replace("+", "")):
                full_num = f"{code}{num.lstrip('0')}"
            else:
                full_num = f"+{num}" if not num.startswith("+") else num
            
            if full_num not in ADDED_NUMBERS_LIST:
                ADDED_NUMBERS_LIST.append(full_num)
                added_count += 1
        
        save_numbers_to_file(ADDED_NUMBERS_LIST)
        bot.reply_to(message, f"✅ Added **{added_count}** numbers for {country_info['name']}!", parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ Invalid numbers.")

@bot.message_handler(func=lambda msg: msg.text in ["📱 My Numbers", "/mynumbers"])
def show_countries_to_user(message):
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = [InlineKeyboardButton(f"{data['name']} ({data['code']})", callback_data=f"get_num_{key}") for key, data in COUNTRIES.items()]
    markup.add(*buttons)
    bot.reply_to(message, "🌍 **Select Country:**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("get_num_") or call.data.startswith("ref_num_"))
def display_numbers_for_user(call):
    country_key = call.data.split("_")[-1]
    country_info = COUNTRIES.get(country_key)
    code = country_info["code"]

    matching_numbers = [n for n in ADDED_NUMBERS_LIST if n.startswith(code)]

    if matching_numbers:
        selected_numbers = random.sample(matching_numbers, min(len(matching_numbers), 8))
        formatted = "\n".join([f"{i+1}. `{num}`" for i, num in enumerate(selected_numbers)])
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔄 Refresh Numbers", callback_data=f"ref_num_{country_key}"))
        markup.add(InlineKeyboardButton("🔙 Back to Countries", callback_data="back_to_countries"))

        bot.answer_callback_query(call.id, f"✅ {country_info['name']}")
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"🎯 **{country_info['name']} Available Numbers:**\n\n{formatted}",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    else:
        bot.answer_callback_query(call.id, f"⚠️ No numbers for {country_info['name']}!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_countries")
def back_to_countries_menu(call):
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = [InlineKeyboardButton(f"{data['name']} ({data['code']})", callback_data=f"get_num_{key}") for key, data in COUNTRIES.items()]
    markup.add(*buttons)
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="🌍 **Select Country:**",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda msg: msg.text in ["📋 Added List", "📋 Added Numbers List"])
def check_added_numbers(message):
    if message.from_user.id != ADMIN_ID: return
    if ADDED_NUMBERS_LIST:
        formatted = "\n".join([f"{i+1}. `{num}`" for i, num in enumerate(ADDED_NUMBERS_LIST)])
        bot.reply_to(message, f"📋 **Added Numbers List ({len(ADDED_NUMBERS_LIST)}):**\n\n{formatted}", parse_mode="Markdown")
    else:
        bot.reply_to(message, "⚠️ No numbers currently stored.")

@bot.message_handler(func=lambda msg: msg.text in ["🗑️ Delete All", "🗑️ Delete All Numbers"])
def confirm_delete_all_numbers(message):
    if message.from_user.id != ADMIN_ID: return
    if not ADDED_NUMBERS_LIST:
        bot.reply_to(message, "⚠️ No numbers stored.")
        return
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Yes, Delete All", callback_data="confirm_delete_all"),
        InlineKeyboardButton("❌ Cancel", callback_data="cancel_delete")
    )
    bot.send_message(message.chat.id, f"⚠️ Delete all {len(ADDED_NUMBERS_LIST)} numbers?", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data in ["confirm_delete_all", "cancel_delete"])
def handle_delete_callback(call):
    if call.from_user.id != ADMIN_ID: return
    if call.data == "confirm_delete_all":
        ADDED_NUMBERS_LIST.clear()
        save_numbers_to_file(ADDED_NUMBERS_LIST)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="✅ Deleted all numbers!")
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="❌ Cancelled.")

@bot.message_handler(func=lambda msg: msg.text == "📥 Check OTP")
def handle_check_otp(message):
    user_id = message.from_user.id
    otp_reward = SETTINGS.get("otp_price", 2.0)
    
    bot.reply_to(message, "🔍 Logging in and fetching OTPs from panel...")
    
    session, err = get_authenticated_session()
    if session:
        otps = fetch_otp_logs(session)
        if otps:
            if user_id in USERS_DB:
                USERS_DB[user_id]["balance"] += otp_reward

            formatted_list = []
            for item in otps[:5]:
                formatted_list.append(
                    f"📱 **Number:** `{item['number']}`\n"
                    f"💬 **Message:** `{item['message']}`\n"
                    f"🔑 **Extracted OTP:** `{item['otp']}`"
                )
            
            response_msg = "📥 **Latest OTP Received:**\n\n" + "\n\n---\n\n".join(formatted_list)
            bot.reply_to(message, response_msg, parse_mode="Markdown")
        else:
            bot.reply_to(message, "ℹ️ No OTP received yet.")
    else:
        bot.reply_to(message, f"❌ Session Login Failed: {err}")

@bot.message_handler(func=lambda msg: msg.text == "👤 Switch to Client Board")
def switch_to_client_board(message):
    if message.from_user.id != ADMIN_ID: return
    bot.send_message(message.chat.id, "🔄 Switched to Client Board!", reply_markup=client_keyboard(is_owner=True))

@bot.message_handler(func=lambda msg: msg.text == "👑 Switch to Owner Board")
def switch_to_owner_board(message):
    if message.from_user.id != ADMIN_ID: return
    bot.send_message(message.chat.id, "👑 Switched to Owner Board!", reply_markup=owner_keyboard())

print("Bot is running...")
while True:
    try:
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        time.sleep(5)

      
