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
    if not filename: return "video"
    return filename

def generate_ai_caption(video_path):
    """
    Video se audio nikal kar Hindi text generate karta hai (First 2 lines only)
    """
    print("🤖 AI generating caption (Listening to audio)...")
    try:
        # Load Whisper Model (Tiny is fast for CPU)
        model = whisper.load_model("tiny")
        
        # Transcribe (Hindi Language Force)
        result = model.transcribe(video_path, language="hi")
        full_text = result['text'].strip()
        
        # Logic: Split text by full stops or pipe (Hindi danda)
        # Hum bas shuru ke 2 sentence uthayenge
        sentences = full_text.replace("।", ".").split(".")
        
        # Top 2 lines lein, agar text chhota hai to pura le lein
        if len(sentences) >= 2:
            short_text = sentences[0].strip() + ".\n" + sentences[1].strip() + "..."
        else:
            short_text = full_text
            
        return short_text
    except Exception as e:
        print(f"⚠️ AI Caption Failed: {e}")
        return "Video Alert!" # Fallback agar AI fail ho jaye

def download_video(url):
    if not os.path.exists(FILES_DIR): os.makedirs(FILES_DIR)
    
    ydl_opts = {
        'format': 'best[ext=mp4]', # MP4 format ensure karein
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
    """
    Direct Video File upload karta hai Telegram par
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram Token missing.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    
    # Format Caption with dots and hashtags
    formatted_caption = f"{caption}\n.\n.\n.\n.\n.{HASHTAGS}"
    
    print("🚀 Sending video to Telegram...")
    try:
        with open(file_path, 'rb') as video_file:
            files = {'video': video_file}
            data = {
                'chat_id': TELEGRAM_CHAT_ID,
                'caption': formatted_caption,
                'parse_mode': 'HTML' # Simple formatting allowed
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
        
        # 1. Download Video
        file_path = download_video(link)
        
        if file_path and os.path.exists(file_path):
            
            # 2. Generate Caption using AI
            ai_text = generate_ai_caption(file_path)
            print(f"📝 Generated Caption: {ai_text}")
            
            # 3. Send Video + Caption to Telegram
            send_video_to_telegram(file_path, ai_text)
            
            # 4. Save History
            with open(HISTORY_FILE, 'a') as f: f.write(link + '\n')
            
            # Cleanup
            os.remove(file_path)
        else:
            print("❌ File not found after download.")

if __name__ == "__main__":
    main()
