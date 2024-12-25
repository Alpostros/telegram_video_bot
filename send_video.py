import os
import json
import telebot
from datetime import datetime
import subprocess

# File paths
TOKEN_FILE = "/home/alpi/videobot/bot_token.txt"  # File containing the bot token
CHAT_IDS_FILE = "/home/alpi/videobot/chat_ids.json"  # File containing chat IDs
VIDEO_DIR = "/home/alpi/videobot/videos"  # Directory to store videos
FINAL_VIDEO_PATH = "/home/alpi/videobot/videos/final_video.mp4"  # Path for final video

def load_bot_token():
    """Load the bot token from a file."""
    if not os.path.exists(TOKEN_FILE):
        raise FileNotFoundError(f"Bot token file not found: {TOKEN_FILE}")
    with open(TOKEN_FILE, "r") as file:
        token = file.read().strip()
    return token

def load_chat_ids():
    """Load chat IDs from the JSON file."""
    if not os.path.exists(CHAT_IDS_FILE):
        print(f"Chat IDs file not found: {CHAT_IDS_FILE}")
        return []
    with open(CHAT_IDS_FILE, "r") as file:
        return json.load(file)

def record_video():
    """Record a 30-second video."""
    os.makedirs(VIDEO_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_video_path = os.path.join(VIDEO_DIR, f"raw_video_{timestamp}.mp4")
    os.system(f"libcamera-vid -t 30000 -o {raw_video_path}")  # 30000 ms = 30 seconds
    return raw_video_path

def convert_video(raw_video_path):
    """Convert the recorded video using ffmpeg."""
    try:
        subprocess.run(
            ["ffmpeg", "-i", raw_video_path, "-c", "copy", FINAL_VIDEO_PATH],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(f"Video converted successfully: {FINAL_VIDEO_PATH}")
        return FINAL_VIDEO_PATH
    except subprocess.CalledProcessError as e:
        print(f"Error converting video: {e}")
        return None

def send_video_to_users(video_path, chat_ids, bot):
    """Send the converted video to all chat IDs."""
    if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
        print("Video file is missing or empty. Aborting.")
        return
    with open(video_path, "rb") as video:
        for chat_id in chat_ids:
            try:
                bot.send_video(chat_id, video)
                print(f"Video sent to chat ID: {chat_id}")
            except Exception as e:
                print(f"Failed to send video to chat ID {chat_id}: {e}")

if __name__ == "__main__":
    try:
        # Load bot token and chat IDs
        bot_token = load_bot_token()
        chat_ids = load_chat_ids()
        
        if not chat_ids:
            print("No chat IDs found. Exiting.")
            exit(1)

        # Initialize the bot
        bot = telebot.TeleBot(bot_token)

        # Record a video
        raw_video_path = record_video()

        # Convert the video using ffmpeg
        final_video_path = convert_video(raw_video_path)

        # Send the converted video to all chat IDs
        if final_video_path:
            send_video_to_users(final_video_path, chat_ids, bot)

        print("Task completed.")
    except Exception as e:
        print(f"An error occurred: {e}")
