import os
import telebot

# Put your bot token here
TOKEN = 'YOUR_BOT_TOKEN_HERE'
bot = telebot.TeleBot(TOKEN)

# Permanent file path to save the QR code
PHOTO_PATH = 'binance_qr.png'

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    btn = telebot.types.InlineKeyboardButton("🛒 Buy Proxy", callback_data='buy_proxy')
    markup.add(btn)
    
    # Check if the user is the owner/admin to customize the message view
    # (Keeping your original logic safe and sound)
    bot.send_message(
        message.chat.id, 
        "👋 Welcome to Proxy Store!\n\n💰 Price: $2.00 (600 PKR)\n\nUse the buttons below to navigate.", 
        reply_markup=markup
    )

# Feature: Automatically saves any photo sent to the bot by the admin
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

@bot.callback_query_handler(func=lambda call: call.data == 'buy_proxy')
def handle_buy_proxy(call):
    # Check if a saved QR photo exists, then send it
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
                                 
