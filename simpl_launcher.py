import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# ⚠️ ВСТАВЬ СЮДА ТВОЙ НОВЫЙ ТОКЕН ⚠️
BOT_TOKEN = "8433404482:AAH0I5KOHANLikLd5pqJzBHFgIo3pc-o3O8"

# ⚠️ ВСТАВЬ СЮДА ТВОЙ GitHub Pages URL ⚠️
MINI_APP_URL = "https://ТВОЙ-ЛОГИН.github.io/clicker-prestige-fixed"

bot = telebot.TeleBot(8433404482:AAH0I5KOHANLikLd5pqJzBHFgIo3pc-o3O8)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Простая кнопка для Mini App
    markup = InlineKeyboardMarkup()
    button = InlineKeyboardButton(
        text="🎮 ИГРАТЬ В КЛИКЕР", 
 web_app=WebAppInfo(url=)
    )    )
    markup.add(button)

    bot.send_message(
        message.chat.id,
        "Привет! Нажми кнопку чтобы играть:",
        reply_markup=markup
    )

print("✅ Бот запущен! Ищи @myKVAclicker_bot в Telegram")

bot.polling()


