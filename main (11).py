import os
import requests
from dotenv import load_dotenv
from yt_dlp import YoutubeDL

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

VIDEO_DIR = "downloads"
os.makedirs(VIDEO_DIR, exist_ok=True)

def read_file(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return [x.strip() for x in f.readlines() if x.strip()]

def write_history(url):
    with open("history.txt", "a") as f:
        f.write(url + "\n")

links = read_file("links.txt")
history = read_file("history.txt")

video_url = None
for link in links:
    if link not in history:
        video_url = link
        break

if not video_url:
    print("No new video found")
    exit()

ydl_opts = {
    "outtmpl": f"{VIDEO_DIR}/video.%(ext)s",
    "format": "mp4",
    "quiet": True
}

with YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(video_url, download=True)
    caption = info.get("description", "") or info.get("title", "")
    video_path = ydl.prepare_filename(info)

# Upload to catbox.moe
with open(video_path, "rb") as f:
    r = requests.post(
        "https://catbox.moe/user/api.php",
        data={"reqtype": "fileupload"},
        files={"fileToUpload": f}
    )

catbox_url = r.text.strip()

# Send to Telegram
telegram_api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
requests.post(
    telegram_api,
    data={
        "chat_id": CHAT_ID,
        "video": catbox_url,
        "caption": caption
    }
)

# Send to Webhook (ONLY VIDEO URL)
requests.post(
    WEBHOOK_URL,
    json={
        "video_url": catbox_url
    }
)

write_history(video_url)
print("✅ Done:", catbox_url)

