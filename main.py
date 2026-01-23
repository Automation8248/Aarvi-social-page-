import os
import requests
import yt_dlp
import whisper
import warnings
from urllib.parse import urlparse, unquote

# Warnings ignore karein (Whisper ke liye)
warnings.filterwarnings("ignore")

# --- Configuration ---
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

FILES_DIR = "downloads"
LINKS_FILE = 'link.txt'
HISTORY_FILE = 'history.txt'

# --- SEO Hashtags ---
HASHTAGS = "\n#viral #trending #motivation #quotes #hindi #reels #explore"

def get_filename_from_url(url):
    path = urlparse(url).path
    filename = unquote(os.path.basename(path))
import os
import requests
import yt_dlp
import cv2
import easyocr
import warnings
from urllib.parse import urlparse, unquote

# Warnings ignore
warnings.filterwarnings("ignore")

# --- Configuration ---
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

FILES_DIR = "downloads"
LINKS_FILE = 'link.txt'
HISTORY_FILE = 'history.txt'

# --- SEO Hashtags ---
HASHTAGS = "\n#viral #trending #motivation #quotes #hindi #reels #explore"

def get_visual_caption_3_words(video_path):
    """
    Video ka screenshot leta hai, Hindi text padhta hai, 
    aur pehle 3 words return karta hai.
    """
    print("👁️ Analyzing Video Frames for Text...")
    
    try:
        # 1. Video Load karein
        cap = cv2.VideoCapture(video_path)
        
        # 2. Frame Calculate karein (Video ke 20% hisse par jayenge taaki text dikhe)
        # Aksar shuru mein fade-in hota hai, isliye thoda aage badh kar padhenge
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        target_frame = int(total_frames * 0.20) 
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            return "Video Status..."

        # 3. EasyOCR se Text Read karein (Hindi + English)
        # 'gpu=False' rakha hai kyunki GitHub Actions par GPU nahi hota
        reader = easyocr.Reader(['hi', 'en'], gpu=False, verbose=False)
        result = reader.readtext(frame, detail=0) # Sirf text chahiye

        # 4. Text Processing (First 3 Words)
        if result:
            # Saare alag-alag tukdo ko ek line mein jodo
            full_text = " ".join(result)
            
            # Words mein todo
            words = full_text.split()
            
            # Pehle 3 words nikalo
            if len(words) >= 3:
                short_caption = f"{words[0]} {words[1]} {words[2]}..."
            elif len(words) > 0:
                short_caption = " ".join(words) + "..."
            else:
                short_caption = "New Video..."
                
            return short_caption
        else:
            return "Watch this..." # Agar koi text detect nahi hua
            
    except Exception as e:
        print(f"⚠️ OCR Error: {e}")
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
            print(f"⬇️ Downloading: {url}")
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename
    except Exception as e:
        print(f"❌ Download Error: {e}")
        return None

def send_video_to_telegram(file_path, caption):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram Token missing.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    
    # Format: Caption + Dots + Hashtags
    formatted_caption = f"{caption}\n.\n.\n.\n.\n.{HASHTAGS}"
    
    print(f"🚀 Sending with Caption: {caption}")
    
    try:
        with open(file_path, 'rb') as video_file:
            files = {'video': video_file}
            data = {
                'chat_id': TELEGRAM_CHAT_ID,
                'caption': formatted_caption,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, files=files, data=data)
            
        if response.status_code == 200:
            print("✅ Video sent successfully!")
        else:
            print(f"❌ Telegram Upload Failed: {response.text}")
    except Exception as e:
        print(f"❌ Telegram Error: {e}")

def main():
    if not os.path.exists(HISTORY_FILE): open(HISTORY_FILE, 'w').close()
    
    with open(HISTORY_FILE, 'r') as f: history = f.read().splitlines()
    
    if not os.path.exists(LINKS_FILE): return
    with open(LINKS_FILE, 'r') as f: links = [l.strip() for l in f if l.strip()]

    for link in links:
        if link in history:
            print(f"Skipping: {link}")
            continue
        
        # 1. Download
        file_path = download_video(link)
        
        if file_path and os.path.exists(file_path):
            
            # 2. OCR Logic (Visual Text Extraction)
            visual_caption = get_visual_caption_3_words(file_path)
            
            # 3. Send
            send_video_to_telegram(file_path, visual_caption)
            
            # 4. History Update
            with open(HISTORY_FILE, 'a') as f: f.write(link + '\n')
            
            os.remove(file_path)
        else:
            print("❌ Download Failed.")

if __name__ == "__main__":
    main()
