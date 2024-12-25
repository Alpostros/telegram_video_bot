import telebot

# Replace with your bot token
BOT_TOKEN = ''

# Initialize the bot
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(func=lambda message: True)
def get_chat_id(message):
    """Respond with the chat ID."""
    chat_id = message.chat.id
    print(f"Your chat ID is: {chat_id}")
    bot.reply_to(message, f"Your chat ID is: {chat_id}")
    exit(0)  # Exit after getting the chat ID

if __name__ == "__main__":
    print("Bot is running. Send any message to the bot to get your chat ID.")
    bot.polling()
