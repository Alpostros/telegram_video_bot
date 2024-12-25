import os
import json
import telebot
from datetime import datetime, timedelta
import threading
import subprocess
import signal
import sys
import time

# Fixed paths relative to the project root
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(PROJECT_ROOT, "config.json")
AUTHORIZED_USERS_FILE = os.path.join(PROJECT_ROOT, "authorized_users.json")
SUBSCRIBED_USERS_FILE = os.path.join(PROJECT_ROOT, "subscribed_users.json")
VIDEO_DIR = os.path.join(PROJECT_ROOT, "videos")
RAW_VIDEO_DIR = os.path.join(VIDEO_DIR, "raw")
CONVERTED_VIDEO_DIR = os.path.join(VIDEO_DIR, "converted")

# Meal times (in HH:MM format)
MEAL_TIMES = ["00:50", "09:00", "13:00", "17:00", "21:00", "23:00"]

# Ensure video directories exist
os.makedirs(RAW_VIDEO_DIR, exist_ok=True)
os.makedirs(CONVERTED_VIDEO_DIR, exist_ok=True)

# Load authorized users
if os.path.exists(AUTHORIZED_USERS_FILE):
    with open(AUTHORIZED_USERS_FILE, "r") as file:
        AUTHORIZED_USERS = json.load(file)
else:
    AUTHORIZED_USERS = []

# Load subscribed users
if os.path.exists(SUBSCRIBED_USERS_FILE):
    with open(SUBSCRIBED_USERS_FILE, "r") as file:
        SUBSCRIBED_USERS = json.load(file)
else:
    SUBSCRIBED_USERS = []

def save_authorized_users():
    """Save authorized users to a JSON file."""
    with open(AUTHORIZED_USERS_FILE, "w") as file:
        json.dump(AUTHORIZED_USERS, file)

def save_subscribed_users():
    """Save subscribed users to a JSON file."""
    with open(SUBSCRIBED_USERS_FILE, "w") as file:
        json.dump(SUBSCRIBED_USERS, file)

def load_config():
    """Load the bot token and secret key from the configuration file."""
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"Config file not found: {CONFIG_FILE}")
    with open(CONFIG_FILE, "r") as file:
        config = json.load(file)
        if "bot_token" not in config or "secret_key" not in config:
            raise ValueError("Config file must contain 'bot_token' and 'secret_key'.")
        return config["bot_token"], config["secret_key"]

# Load bot configuration
bot_token, secret_key = load_config()

# Initialize bot
bot = telebot.TeleBot(bot_token)

def log(message):
    """Log a message with a timestamp."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def is_authorized(chat_id):
    """Check if a user is authorized."""
    return chat_id in AUTHORIZED_USERS

@bot.message_handler(commands=['start'])
def start(message):
    """Handle the /start command."""
    bot.reply_to(message, "Welcome! Use /authorize <password> to gain access.")

@bot.message_handler(commands=['authorize'])
def authorize(message):
    """Handle the /authorize command."""
    try:
        password = message.text.split()[1]
        if password == secret_key:
            if message.chat.id not in AUTHORIZED_USERS:
                AUTHORIZED_USERS.append(message.chat.id)
                save_authorized_users()
                bot.reply_to(message, "You are now authorized!")
                send_available_commands(message.chat.id)
                log(f"User authorized: {message.chat.id}")
            else:
                bot.reply_to(message, "You are already authorized.")
                send_available_commands(message.chat.id)
        else:
            bot.reply_to(message, "Incorrect password.")
    except IndexError:
        bot.reply_to(message, "Usage: /authorize <password>")

def send_available_commands(chat_id):
    """Send the list of available commands to the user."""
    commands = [
        "/getvideo - Send a 30-second video",
        "/subscribe - Subscribe to meal-time videos",
        "/unsubscribe - Unsubscribe from meal-time videos",
        "/authorize <password> - Authorize yourself",
        "/start - See the welcome message",
    ]
    bot.send_message(chat_id, "Here are the available commands:\n" + "\n".join(commands))

@bot.message_handler(commands=['getvideo'])
def get_video(message):
    """Handle the /getvideo command."""
    if not is_authorized(message.chat.id):
        bot.reply_to(message, "Unauthorized. Use /authorize <password>.")
        return
    try:
        bot.reply_to(message, "Recording video. Please wait...")
        raw_video_path = record_video(30)
        final_video_path = convert_video(raw_video_path)
        with open(final_video_path, "rb") as video:
            bot.send_video(message.chat.id, video)
        log(f"Video sent to chat ID: {message.chat.id}")
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")
        log(f"Error handling /getvideo: {e}")

@bot.message_handler(commands=['subscribe'])
def subscribe(message):
    """Handle the /subscribe command."""
    if not is_authorized(message.chat.id):
        bot.reply_to(message, "Unauthorized. Use /authorize <password>.")
        return
    if message.chat.id not in SUBSCRIBED_USERS:
        SUBSCRIBED_USERS.append(message.chat.id)
        save_subscribed_users()
        bot.reply_to(message, "You have subscribed to scheduled videos!")
        log(f"User subscribed: {message.chat.id}")
    else:
        bot.reply_to(message, "You are already subscribed.")

@bot.message_handler(commands=['unsubscribe'])
def unsubscribe(message):
    """Handle the /unsubscribe command."""
    if message.chat.id in SUBSCRIBED_USERS:
        SUBSCRIBED_USERS.remove(message.chat.id)
        save_subscribed_users()
        bot.reply_to(message, "You have unsubscribed from scheduled videos.")
        log(f"User unsubscribed: {message.chat.id}")
    else:
        bot.reply_to(message, "You are not subscribed.")

def record_video(duration):
    """Record a video of specified duration at 1280x720 resolution."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_path = os.path.join(RAW_VIDEO_DIR, f"raw_video_{timestamp}.h264")
    try:
        subprocess.run(
            [
                "libcamera-vid",
                "-t", str(duration * 1000),
                "--codec", "h264",
                "--width", "1280",
                "--height", "720",
                "-o", raw_path
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        log(f"Video recorded successfully: {raw_path}")
    except subprocess.CalledProcessError as e:
        log(f"Error during recording: {e}")
        raise
    return raw_path

def convert_video(raw_video_path):
    """Convert raw video to MP4 format and delete the raw video after conversion."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    converted_path = os.path.join(CONVERTED_VIDEO_DIR, f"video_{timestamp}.mp4")
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i", raw_video_path,
                "-c:v", "copy",
                converted_path
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        log(f"Video converted successfully: {converted_path}")
    except subprocess.CalledProcessError as e:
        log(f"Error during conversion: {e}")
        raise
    finally:
        if os.path.exists(raw_video_path):
            os.remove(raw_video_path)
            log(f"Deleted raw video: {raw_video_path}")
    return converted_path

def cleanup_old_videos():
    """Delete videos older than 2 days."""
    now = datetime.now()
    for file in os.listdir(CONVERTED_VIDEO_DIR):
        file_path = os.path.join(CONVERTED_VIDEO_DIR, file)
        if os.path.isfile(file_path):
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if now - file_time > timedelta(days=2):
                os.remove(file_path)
                log(f"Deleted old video: {file_path}")

def send_scheduled_videos():
    """Send videos at meal times."""
    while True:
        cleanup_old_videos()
        now = datetime.now().strftime("%H:%M")
        if now in MEAL_TIMES:
            log(f"Sending video for meal time: {now}")
            try:
                raw_video_path = record_video(30)
                final_video_path = convert_video(raw_video_path)
                for chat_id in SUBSCRIBED_USERS:
                    with open(final_video_path, "rb") as video:
                        bot.send_video(chat_id, video)
                log(f"Sent video to subscribed users: {SUBSCRIBED_USERS}")
                time.sleep(60)
            except Exception as e:
                log(f"Error sending scheduled video: {e}")
        time.sleep(1)

def shutdown(signal, frame):
    """Gracefully shut down the bot."""
    log("Shutting down bot...")
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

# Set command hints for Telegram
bot.set_my_commands([
    telebot.types.BotCommand("getvideo", "Send a 30-second video"),
    telebot.types.BotCommand("subscribe", "Subscribe to meal-time videos"),
    telebot.types.BotCommand("unsubscribe", "Unsubscribe from meal-time videos"),
    telebot.types.BotCommand("authorize", "Authorize yourself"),
    telebot.types.BotCommand("start", "Start and see the welcome message"),
])

# Start the scheduled video thread
threading.Thread(target=send_scheduled_videos, daemon=True).start()

# Start the bot
log("Bot is running. Waiting for commands...")
bot.polling()