import os
import requests
import yt_dlp
import cv2
import pytesseract
import time
import random

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

FILES_DIR = "downloads"
LINKS_FILE = 'link.txt'
HISTORY_FILE = 'history.txt'
HASHTAGS = "\n#viral #trending #motivation #quotes #hindi #reels #explore"

# --- BYPASS ENGINE (COBALT API) ---
def get_bypass_link(insta_url):
    """
    Instagram Block Bypass karne ke liye Cobalt API ka use karta hai.
    Ye direct MP4 link return karega.
    """
    api_url = "https://api.cobalt.tools/api/json"
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    data = {
        "url": insta_url,
        "vQuality": "720",
        "filenamePattern": "basic"
    }

    print("🛡️ Bypassing Instagram Security...")
    try:
        response = requests.post(api_url, json=data, headers=headers, timeout=15)
        response_data = response.json()

        if response_data.get('status') == 'stream':
            return response_data.get('url')
        elif response_data.get('status') == 'redirect':
            return response_data.get('url')
        elif response_data.get('status') == 'picker':
            # Agar multiple items hain (Carousel), to pehla video uthao
            return response_data['picker'][0]['url']
        else:
            print(f"❌ Bypass API Error: {response_data}")
            return None
    except Exception as e:
        print(f"❌ Bypass Failed: {e}")
        return None

# --- OCR LOGIC ---
def get_visual_caption(video_path):
    print("👁️ Scanning video text...")
    try:
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames == 0: return "New Reel..."

        # 20% point par frame capture
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(total_frames * 0.20))
        ret, frame = cap.read()
        cap.release()

        if not ret: return "Reel Video..."

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray, lang='eng') # English script se Hindi padhne ki koshish (fast)
        
        words = text.split()
        if len(words) >= 3:
            return f"{words[0]} {words[1]} {words[2]}..."
        elif len(words) > 0:
            return " ".join(words) + "..."
        else:
            return "Must Watch..."
            
    except:
        return "Trending Reel..."

# --- DOWNLOAD LOGIC ---
def download_video_file(direct_url):
    if not os.path.exists(FILES_DIR): os.makedirs(FILES_DIR)
    
    filename = f"{FILES_DIR}/video_{int(time.time())}.mp4"
    
    try:
        print("⬇️ Downloading Video File...")
        with requests.get(direct_url, stream=True) as r:
            r.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return filename
    except Exception as e:
        print(f"❌ Download Error: {e}")
        return None

# --- SEND LOGIC ---
def send_to_telegram(file_path, caption):
    if not TELEGRAM_BOT_TOKEN: return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    formatted_caption = f"{caption}\n.\n.\n.\n.\n.{HASHTAGS}"
    
    print("🚀 Sending to Telegram...")
    try:
        with open(file_path, 'rb') as f:
            requests.post(url, 
                files={'video': f}, 
                data={'chat_id': TELEGRAM_CHAT_ID, 'caption': formatted_caption}
            )
            print("✅ Sent Successfully!")
    except Exception as e:
        print(f"❌ Send Error: {e}")

def main():
    if not os.path.exists(HISTORY_FILE): open(HISTORY_FILE, 'w').close()
    with open(HISTORY_FILE, 'r') as f: history = f.read().splitlines()
    
    if not os.path.exists(LINKS_FILE): 
        print("Link file missing")
        return
        
    with open(LINKS_FILE, 'r') as f: links = [l.strip() for l in f if l.strip()]

    if not links:
        print("No links found.")
        return

    for link in links:
        if link in history: 
            print(f"Skipping: {link}")
            continue
        
        print(f"Processing Insta Link: {link}")
        
        # STEP 1: Get Bypass Link (Direct MP4)
        mp4_url = get_bypass_link(link)
        
        if mp4_url:
            # STEP 2: Download
            file_path = download_video_file(mp4_url)
            
            if file_path:
                # STEP 3: OCR & Send
                caption = get_visual_caption(file_path)
                send_to_telegram(file_path, caption)
                
                # History Update
                with open(HISTORY_FILE, 'a') as f: f.write(link + '\n')
                os.remove(file_path)
            else:
                print("Download failed.")
        else:
            print("❌ Could not bypass Instagram block.")

if __name__ == "__main__":
    main()
