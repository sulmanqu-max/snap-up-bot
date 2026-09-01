import os
import telebot

# Put your bot token here
TOKEN = 'YOUR_BOT_TOKEN_HERE'
bot = telebot.TeleBot(TOKEN)

# Permanent file path to save the QR code
PHOTO_PATH = 'binance_qr.png'

# Your original /start command and logic (kept safe)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    btn = telebot.types.InlineKeyboardButton("🛒 Buy Proxy", callback_data='buy_proxy')
    markup.add(btn)
    
    bot.send_message(
        message.chat.id, 
        "👋 Welcome to Proxy Store!\n\n💰 Price: $2.00 (600 PKR)\n\nUse the buttons below to navigate.", 
        reply_markup=markup
    )

# NEW FEATURE: Automatically saves any photo sent to the bot
@bot.message_handler(content_types=['photo'])
def save_qr_photo(message):
    try:
        # Download the highest quality version of the photo
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Save it locally in the container storage
        with open(PHOTO_PATH, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        bot.reply_to(
            message, 
            "✅ Binance QR Code Successfully Saved!\nNow when users click 'Buy Proxy', this exact photo will be sent automatically."
        )
    except Exception as e:
        bot.reply_to(message, f"❌ Error saving photo: {e}")

# Updated callback to send the saved photo when users click 'Buy Proxy'
@bot.callback_query_handler(func=lambda call: call.data == 'buy_proxy')
def handle_buy_proxy(call):
    if os.path.exists(PHOTO_PATH):
        with open(PHOTO_PATH, 'rb') as photo:
            bot.send_photo(
                call.message.chat.id, 
                photo, 
                caption="👑 Scan the QR code above to make payment for your proxy."
            )
    else:
        bot.send_message(
            call.message.chat.id, 
            "⚠️ QR code has not been uploaded yet. Please send the payment QR code photo to the bot first."
        )

bot.infinity_polling()
import telebot
from telebot import types
import time
import requests

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8861291494:AAFkrLAg2IjcPtQ3FIEJbAwW_hIzJrNJTgg" 
OWNER_ID = 8112208075  # Verified Owner ID
BINANCE_PAY_LINK = "https://s.binance.com/I2d3m5I2"

# Global variables
QR_FILE_ID = None
admin_temp_state = {}

price_settings = {
    "USD": "2.00",
    "PKR": "600",
    "DATA": "200 MB"
}

proxy_stock = {}
verified_users = set()

def get_country_flag_and_name(text):
    text = text.strip().upper()
    
    country_map = {
        "USA": ("🇺🇸", "USA"), "US": ("🇺🇸", "USA"), "UNITED STATES": ("🇺🇸", "USA"),
        "UK": ("🇬🇧", "UK"), "GB": ("🇬🇧", "UK"), "UNITED KINGDOM": ("🇬🇧", "UK"),
        "PH": ("🇵🇭", "PHILIPPINES"), "PHILIPPINES": ("🇵🇭", "PHILIPPINES"),
        "PK": ("🇵🇰", "PAKISTAN"), "PAKISTAN": ("🇵🇰", "PAKISTAN"),
        "IN": ("🇮🇳", "INDIA"), "INDIA": ("🇮🇳", "INDIA"),
        "AE": ("🇦🇪", "UAE"), "UAE": ("🇦🇪", "UAE"), "DUBAI": ("🇦🇪", "UAE"),
        "CA": ("🇨🇦", "CANADA"), "CANADA": ("🇨🇦", "CANADA"),
        "AU": ("🇦🇺", "AUSTRALIA"), "AUSTRALIA": ("🇦🇺", "AUSTRALIA"),
        "DE": ("🇩🇪", "GERMANY"), "GERMANY": ("🇩🇪", "GERMANY"),
        "FR": ("🇫🇷", "FRANCE"), "FRANCE": ("🇫🇷", "FRANCE"),
        "SA": ("🇸🇦", "SAUDI ARABIA"), "SAUDI ARABIA": ("🇸🇦", "SAUDI ARABIA")
    }
    
    if text in country_map:
        return country_map[text]
    
    if len(text) == 2 and text.isalpha():
        flag = chr(ord(text[0]) + 127397) + chr(ord(text[1]) + 127397)
        return flag, text
        
    return "🌍", text

bot = telebot.TeleBot(BOT_TOKEN)

def get_main_reply_keyboard(is_owner=False):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_buy = types.KeyboardButton("🛒 Buy Proxy")
    btn_help = types.KeyboardButton("❓ Help & Support")
    btn_info = types.KeyboardButton("ℹ️ Account Info")
    
    if is_owner:
        btn_add_proxy = types.KeyboardButton("➕ Add Proxy")
        btn_stock = types.KeyboardButton("📊 Check Stock")
        markup.add(btn_buy, btn_help, btn_info, btn_add_proxy, btn_stock)
    else:
        markup.add(btn_buy, btn_help, btn_info)
        
    return markup

def verify_binance_screenshot(file_url):
    try:
        ocr_url = f"https://api.ocr.space/parse/imageurl?apikey=helloworld&url={file_url}"
        response = requests.get(ocr_url, timeout=10)
        result = response.json()
        
        if result.get("IsErroredOnProcessing"):
            return False, "Error"
            
        parsed_text = result["ParsedResults"][0]["ParsedText"].lower()
        keywords = ["binance", "completed", "successful", "paid", "order", "transfer"]
        matched_count = sum(1 for word in keywords if word in parsed_text)
        
        if matched_count >= 2:
            return True, "Valid"
        else:
            return False, "Invalid"
            
    except Exception as e:
        print(f"OCR Error: {e}")
        return False, "Error"

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    is_owner = (user_id == OWNER_ID)
    
    welcome_text = (
        f"👋 **Welcome {message.from_user.first_name} to Proxy Store!**\n\n"
        f"📦 **Package:** {price_settings['DATA']} High-Speed Proxy\n"
        f"💵 **Price:** ${price_settings['USD']} ({price_settings['PKR']} PKR)\n\n"
        "Use the buttons below to navigate."
    )
    
    bot.send_message(
        message.chat.id, 
        welcome_text, 
        parse_mode="Markdown", 
        reply_markup=get_main_reply_keyboard(is_owner)
    )

@bot.message_handler(content_types=['photo'], func=lambda m: m.from_user.id == OWNER_ID and m.from_user.id not in admin_temp_state)
def save_owner_qr_photo(message):
    global QR_FILE_ID
    QR_FILE_ID = message.photo[-1].file_id
    bot.reply_to(
        message, 
        "✅ **Binance QR Code Successfully Saved!**", 
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text == "🛒 Buy Proxy")
def handle_buy_proxy(message):
    user_id = message.from_user.id
    if user_id == OWNER_ID:
        markup = types.InlineKeyboardMarkup()
        if proxy_stock:
            for country in proxy_stock.keys():
                markup.add(types.InlineKeyboardButton(f"📥 Get {country} Proxy (Free)", callback_data=f"claim_{country}"))
        else:
            markup.add(types.InlineKeyboardButton("➕ Add Proxy First", callback_data="go_add_proxy"))

        bot.send_message(
            message.chat.id, 
            "👑 **Admin Access:** You are the owner, so proxies are completely **free** for you! Select a country below to get your proxy instantly:", 
            parse_mode="Markdown",
            reply_markup=markup
        )
        return

    markup = types.InlineKeyboardMarkup()
    btn_pay = types.InlineKeyboardButton("💳 Open Binance Pay Link", url=BINANCE_PAY_LINK)
    markup.add(btn_pay)

    pay_caption = (
        f"💳 **Binance Payment Details**\n\n"
        f"💵 **Amount:** ${price_settings['USD']} ({price_settings['PKR']} PKR)\n"
        f"👤 **Merchant ID:** `User-f44355db`\n\n"
        "📲 **Scan the QR Code image using Binance App to pay.**\n"
        "🔗 Or click the direct Pay Link button below.\n\n"
        "📸 **After completing payment, please send the screenshot here.**"
    )
    
    global QR_FILE_ID
    if QR_FILE_ID:
        try:
            bot.send_photo(
                message.chat.id, 
                photo=QR_FILE_ID, 
                caption=pay_caption, 
                parse_mode="Markdown", 
                reply_markup=markup
            )
            return
        except Exception as e:
            print(f"Error sending photo: {e}")
            
    bot.send_message(
        message.chat.id, 
        pay_caption, 
        parse_mode="Markdown", 
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == "❓ Help & Support")
def handle_help(message):
    help_text = (
        "📌 **How to Buy:**\n"
        "1️⃣ Click **🛒 Buy Proxy** & pay via Binance.\n"
        "2️⃣ Send the payment screenshot in chat.\n"
        "3️⃣ Bot will auto-verify or send to admin for approval.\n"
        "4️⃣ Type your desired Country Code (e.g., USA, PH, PK) to get proxy!"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "ℹ️ Account Info")
def handle_account_info(message):
    uid = message.from_user.id
    if uid == OWNER_ID:
        status = "Store Owner 👑 (Free Access)"
    else:
        status = "Verified Customer ✅" if uid in verified_users else "Unverified ❌"
        
    info_text = (
        f"👤 **User Info:**\n\n"
        f"Name: {message.from_user.first_name}\n"
        f"ID: `{uid}`\n"
        f"Status: {status}"
    )
    bot.send_message(message.chat.id, info_text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "➕ Add Proxy")
def handle_add_proxy_button(message):
    if message.from_user.id != OWNER_ID:
        return
        
    admin_temp_state[OWNER_ID] = {"step": "waiting_country_name"}
    bot.send_message(
        message.chat.id,
        "🌍 **Enter Country Name or Code:**\n\n*(Example: USA, PH, UK, PK, etc.)*",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text == "📊 Check Stock")
def handle_check_stock(message):
    if message.from_user.id != OWNER_ID:
        return
    if not proxy_stock:
        bot.send_message(message.chat.id, "📊 **No proxies available in stock right now.**", parse_mode="Markdown")
        return
    stock_text = "📊 **Available Proxy Stock:**\n\n"
    for country, items in proxy_stock.items():
        stock_text += f"🌍 **{country}**: `{len(items)}` proxies available\n"
    bot.send_message(message.chat.id, stock_text, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'], func=lambda m: m.from_user.id != OWNER_ID)
def handle_screenshot(message):
    user_id = message.from_user.id
    status_msg = bot.reply_to(message, "🔍 **Scanning payment screenshot... Please wait...**")

    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

        is_valid, _ = verify_binance_screenshot(file_url)

        if is_valid:
            verified_users.add(user_id)
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text="🎉 **Payment Verified Successfully by Bot!** ✅\n\n"
                     "🌍 **Now please type the name or code of the country whose proxy you want** "
                     "(e.g., `PH`, `USA`, `UK`, `PK`, etc.):",
                parse_mode="Markdown"
            )
            bot.send_message(
                OWNER_ID, 
                f"🤖 **Auto-Verified Payment!**\nUser: @{message.from_user.username} (ID: `{user_id}`)", 
                parse_mode="Markdown"
            )
        else:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text="⏳ **Payment screenshot sent to Admin for manual review!**\nPlease wait a moment, Admin will verify shortly.",
                parse_mode="Markdown"
            )
            
            markup = types.InlineKeyboardMarkup()
            btn_approve = types.InlineKeyboardButton("✅ Approve User", callback_data=f"approve_{user_id}")
            markup.add(btn_approve)

            bot.send_message(
                OWNER_ID,
                f"🚨 **Pending Payment Review!**\n"
                f"👤 User: {message.from_user.first_name} (@{message.from_user.username})\n"
                f"🆔 ID: `{user_id}`\n\n"
                f"👇 Click the button below to approve this user:",
                parse_mode="Markdown"
            )
            bot.forward_message(OWNER_ID, message.chat.id, message.message_id, reply_markup=markup)

    except Exception as e:
        print(f"Error in screenshot handling: {e}")
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text="❌ **Error processing screenshot.** Please try sending it again or contact support.",
            parse_mode="Markdown"
        )

@bot.message_handler(func=lambda message: message.chat.type == 'private' and not message.text.startswith('/') and message.text not in ["🛒 Buy Proxy", "❓ Help & Support", "ℹ️ Account Info", "➕ Add Proxy", "📊 Check Stock"])
def handle_text_messages(message):
    user_id = message.from_user.id
    text_input = message.text.strip()
    
    if user_id == OWNER_ID:
        if user_id in admin_temp_state:
            state = admin_temp_state[user_id].get("step")
            
            if state == "waiting_country_name":
                flag, c_name = get_country_flag_and_name(text_input)
                formatted_country = f"{flag} {c_name}"
                
                admin_temp_state[user_id] = {"step": "waiting_proxy_details", "country": formatted_country}
                
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton(f"➕ Add Proxy for {formatted_country}", callback_data=f"add_for_{formatted_country}"))
                
                bot.reply_to(
                    message,
                    f"🎯 **Country Set:** {formatted_country}\n\n👇 Click the button below to proceed:",
                    parse_mode="Markdown",
                    reply_markup=markup
                )
                return
                
            elif state == "waiting_proxy_details":
                country = admin_temp_state.get(user_id, {}).get("country", "🌍 Unknown")
                proxy_data = text_input
                
                if country not in proxy_stock:
                    proxy_stock[country] = []
                    
                proxy_stock[country].append(proxy_data)
                if user_id in admin_temp_state:
                    del admin_temp_state[user_id]
                
                bot.reply_to(
                    message, 
                    f"✅ **Proxy Added Successfully!**\n\n🌍 **Country:** {country}\n📦 **Total Stock:** `{len(proxy_stock[country])}`", 
                    parse_mode="Markdown"
                )
                return

    if user_id != OWNER_ID and user_id not in verified_users:
        bot.reply_to(message, "⚠️ **Please send payment screenshot first or wait for Admin approval.**")
        return

    flag, c_name = get_country_flag_and_name(text_input)
    final_country_name = f"{flag} {c_name}"

    markup = types.InlineKeyboardMarkup()
    btn_get = types.InlineKeyboardButton(f"⚡ Get 1 {final_country_name} Proxy", callback_data=f"claim_{final_country_name}")
    markup.add(btn_get)

    bot.reply_to(
        message,
        f"🎯 **Your Selection:** `{final_country_name}`\n\nClick the button below to receive your proxy:",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def admin_approve_user(call):
    if call.from_user.id != OWNER_ID:
        return
        
    target_user_id = int(call.data.replace("approve_", ""))
    verified_users.add(target_user_id)
    
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
    bot.send_message(call.message.chat.id, f"✅ **User (ID: `{target_user_id}`) has been approved successfully!**", parse_mode="Markdown")
    
    try:
        bot.send_message(
            target_user_id,
            "🎉 **Your Payment Has Been Approved by Admin!** ✅\n\n"
            "🌍 **Now please type the name or code of the country whose proxy you want** "
            "(e.g., `PH`, `USA`, `UK`, `PK`, etc.):",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Could not message user {target_user_id}: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "go_add_proxy")
def go_add_proxy_callback(call):
    if call.from_user.id != OWNER_ID:
        return
    admin_temp_state[OWNER_ID] = {"step": "waiting_country_name"}
    bot.send_message(
        call.message.chat.id,
        "🌍 **Enter Country Name or Code:**\n\n*(Example: USA, PH, UK, PK, etc.)*",
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("add_for_"))
def admin_click_add_button(call):
    if call.from_user.id != OWNER_ID:
        return
        
    country = call.data[8:] 
    admin_temp_state[OWNER_ID] = {"step": "waiting_proxy_details", "country": country}
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"🎯 Target Country: **{country}**\n\n"
             "📝 Now send the proxy details in this format:\n"
             "`socks5://...` or `IP:Port:Username:Password`",
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("claim_"))
def claim_single_proxy(call):
    country_name = call.data[6:] 
    user_id = call.from_user.id

    if user_id != OWNER_ID and user_id in verified_users:
        verified_users.remove(user_id)

    available_proxies = proxy_stock.get(country_name, [])

    if available_provenes := available_proxies: # safe reference
        raw_proxy = available_proxies.pop(0)
        
        msg = (
            f"🎉 **Here is your Proxy Details!**\n"
            f"🌍 **Country:** {country_name}\n\n"
            f"🔗 **Proxy Link / Details:**\n`{raw_proxy}`\n\n"
            f"📋 *Tap the text above to copy it directly!*"
        )
        
        bot.send_message(user_id, msg, parse_mode="Markdown")
        if user_id != OWNER_ID:
            bot.send_message(OWNER_ID, f"✅ Issued 1 **{country_name}** proxy to user `{user_id}`")
    else:
        bot.send_message(
            user_id, 
            f"⏳ **Request Received for {country_name}!**\nProxy currently out of stock. Admin will send it to you shortly.",
            parse_mode="Markdown"
        )
        if user_id != OWNER_ID:
            bot.send_message(OWNER_ID, f"🚨 **User `{user_id}` requested {country_name} proxy (Out of Stock!).**")

@bot.message_handler(commands=['setprice'])
def set_price(message):
    if message.from_user.id != OWNER_ID:
        return
    try:
        parts = message.text.split(" ")
        price_settings["USD"] = parts[1]
        price_settings["PKR"] = parts[2]
        bot.reply_to(message, f"✅ Updated Price Successfully:\n💵 **${parts[1]} ({parts[2]} PKR)**", parse_mode="Markdown")
    except IndexError:
        bot.reply_to(message, "❌ **Usage Format:**\n`/setprice 3.00 900`", parse_mode="Markdown")

if __name__ == "__main__":
    print("Connecting to Telegram...")
    try:
        me = bot.get_me()
        print(f"✅ Bot Connected Successfully: @{me.username}")
        bot.infinity_polling(timeout=30, long_polling_timeout=20)
    except Exception as e:
        print(f"❌ Connection Error: {e}")
