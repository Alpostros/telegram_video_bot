
# Telegram Video Bot

A Python-based Telegram bot that records and sends videos using `libcamera-vid` on Raspberry Pi. The bot supports:

- Manual video recording and sending via `/getvideo`.
- Scheduled video recording and sending at specified meal times.
- User authorization and subscription management.
- Automatic cleanup of old video files.

---

## Features

- **Manual Video Recording**: Users can request a 30-second video using `/getvideo`.
- **Scheduled Videos**: Videos are automatically recorded and sent to subscribed users at predefined meal times.
- **User Authorization**: Only authorized users can access the bot's features.
- **Video Management**:
  - Converts raw `.h264` videos to `.mp4`.
  - Cleans up old `.mp4` videos after 2 days.
- **Graceful Shutdown**: Handles system signals for clean exit.

---

## Prerequisites

### Hardware
- Raspberry Pi 4 or similar with a compatible camera module.
- Raspberry Pi OS (`bullseye` recommended).

### Software
- Python 3.7 or newer.
- `libcamera-vid` for video recording.
- `ffmpeg` for video conversion.

### Dependencies
Install `libcamera` and `ffmpeg`:
```bash
sudo apt update
sudo apt install libcamera-apps ffmpeg
```

Install Python dependencies:
```bash
pip install pyTelegramBotAPI
```

---

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd <repository-name>
```

### 2. Set Up the Environment
Ensure the following directories exist:
- `videos/raw`: For storing raw `.h264` video files.
- `videos/converted`: For storing converted `.mp4` files.

Run:
```bash
mkdir -p videos/raw videos/converted
```

### 3. Configure the Bot
Create a `config.json` file in the project root:
```json
{
    "bot_token": "your_bot_token_here",
    "secret_key": "your_secret_key_here"
}
```
- Replace `"your_bot_token_here"` with your Telegram bot token.
- Replace `"your_secret_key_here"` with a password for user authorization.

---

## Running the Bot

### 1. Run the Bot
```bash
python3 send_video.py
```

### 2. Start the Bot on System Boot (Optional)
You can create a systemd service to start the bot automatically.

1. Create a service file:
   ```bash
   sudo nano /etc/systemd/system/video-bot.service
   ```

2. Add the following content:
   ```ini
   [Unit]
   Description=Telegram Video Bot
   After=network.target

   [Service]
   WorkingDirectory=/path/to/your/project
   ExecStart=/usr/bin/python3 send_video.py
   Restart=always
   User=pi

   [Install]
   WantedBy=multi-user.target
   ```

3. Reload systemd and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start video-bot.service
   sudo systemctl enable video-bot.service
   ```

---

## Usage

### Available Commands

- `/start`: Display a welcome message.
- `/authorize <password>`: Authorize the user to access the bot.
- `/getvideo`: Record and send a 30-second video.
- `/subscribe`: Subscribe to scheduled videos at meal times.
- `/unsubscribe`: Unsubscribe from scheduled videos.

### Meal Times
Videos are recorded and sent at the following times:
- **00:50**, **09:00**, **13:00**, **17:00**, **21:00**, **23:00**

### Logs
All logs are printed to the console with timestamps. Use a logging tool or redirect output to a file for persistent logs:
```bash
python3 send_video.py > bot.log 2>&1 &
```

---

## File Structure

```plaintext
/project-root
│
├── config.json                  # Bot configuration file
├── authorized_users.json        # Authorized users (auto-generated)
├── subscribed_users.json        # Subscribed users (auto-generated)
├── videos/                      # Video storage directory
│   ├── raw/                     # Raw .h264 videos
│   └── converted/               # Converted .mp4 videos
├── send_video.py                # Main bot script
└── README.md                    # Project documentation
```

---

## Troubleshooting

### Common Errors

1. **No Cameras Available**
   - Ensure the camera is enabled:
     ```bash
     sudo raspi-config
     ```
     Go to **Interface Options** > **Camera** > Enable.
   - Test the camera:
     ```bash
     libcamera-vid --list-cameras
     ```

2. **`FileNotFoundError: Config file not found`**
   - Ensure `config.json` exists in the project root and is correctly configured.

3. **Bot Crashes or Freezes**
   - Check the logs for detailed error messages.
   - Ensure all required dependencies are installed.

---

## Contributing

Feel free to submit issues or pull requests to improve this project.

---

## License

This project is licensed under the MIT License. See `LICENSE` for more details.
