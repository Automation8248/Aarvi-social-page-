import os
import requests
import yt_dlp
import cv2
import pytesseract
from urllib.parse import urlparse, unquote

# --- Config ---
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

FILES_DIR = "downloads"
LINKS_FILE = 'link.txt'
HISTORY_FILE = 'history.txt'
HASHTAGS = "\n#viral #trending #motivation #quotes #hindi #reels #explore"

def get_visual_caption(video_path):
    """Video ke frame se text nikalta hai (Fast Mode using Tesseract)"""
    print("👁️ Scanning video for text...")
    try:
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Video ke 20% hisse par jump karo (Intro skip karne ke liye)
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(total_frames * 0.20))
        ret, frame = cap.read()
        cap.release()

        if not ret: return "Video Status..."

        # Image ko Black & White karo (Faster OCR processing)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Text Read karo
        text = pytesseract.image_to_string(gray, lang='eng') # Hindi pack heavy hota hai, English text fast pakdega
        
        # Processing words
        words = text.split()
        if len(words) >= 3:
            return f"{words[0]} {words[1]} {words[2]}..."
        elif len(words) > 0:
            return " ".join(words) + "..."
        else:
            return "Watch this..."
            
    except Exception as e:
        print(f"OCR Error: {e}")
        return "New Reel..."

def download_video(url):
    if not os.path.exists(FILES_DIR): os.makedirs(FILES_DIR)
    ydl_opts = {
        'format': 'best[ext=mp4]',
        'outtmpl': f'{FILES_DIR}/%(title)s.%(ext)s',
        'quiet': True,
        'restrictfilenames': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"⬇️ Downloading...")
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except:
        return None

def send_to_telegram(file_path, caption):
    if not TELEGRAM_BOT_TOKEN: return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    formatted_caption = f"{caption}\n.\n.\n.\n.\n.{HASHTAGS}"
    
    print("🚀 Sending...")
    try:
        with open(file_path, 'rb') as f:
            requests.post(url, 
                files={'video': f}, 
                data={'chat_id': TELEGRAM_CHAT_ID, 'caption': formatted_caption}
            )
            print("✅ Sent!")
    except Exception as e:
        print(f"Send Fail: {e}")

def main():
    if not os.path.exists(HISTORY_FILE): open(HISTORY_FILE, 'w').close()
    with open(HISTORY_FILE, 'r') as f: history = f.read().splitlines()
    if not os.path.exists(LINKS_FILE): return
    with open(LINKS_FILE, 'r') as f: links = [l.strip() for l in f if l.strip()]

    for link in links:
        if link in history: continue
        
        file_path = download_video(link)
        if file_path:
            caption = get_visual_caption(file_path)
            send_to_telegram(file_path, caption)
            
            with open(HISTORY_FILE, 'a') as f: f.write(link + '\n')
            os.remove(file_path)

if __name__ == "__main__":
    main()
