import os
import requests
import sys
import glob
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from deep_translator import GoogleTranslator

# --- CONFIGURATION ---
VIDEO_LIST_FILE = 'videos.txt'
HISTORY_FILE = 'history.txt'

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

def clean_url(url):
    return url.strip().strip('"').strip("'").strip(',')

def get_next_video():
    processed = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            processed = [clean_url(l) for l in f.readlines()]
    with open(VIDEO_LIST_FILE, 'r') as f:
        all_urls = [clean_url(l) for l in f.readlines() if l.strip()]
    for url in all_urls:
        if url not in processed: return url
    return None

def get_video_link_via_browser(url):
    print(f"🌐 Opening Headless Chrome for: {url}")
    chrome_options = Options()
    chrome_options.add_argument("--headless") # Browser dikhega nahi
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    video_src = None
    try:
        driver.get(url)
        time.sleep(7) # Page load hone ka wait
        
        # Video tag dhoondhna
        videos = driver.find_elements("tag name", "video")
        if videos:
            video_src = videos[0].get_attribute("src")
            print("✅ Direct Video Link Found!")
    except Exception as e:
        print(f"❌ Browser Error: {e}")
    finally:
        driver.quit()
    return video_src

def download_video(video_url):
    print("📥 Downloading video file...")
    filename = "temp_video.mp4"
    r = requests.get(video_url, stream=True)
    with open(filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: f.write(chunk)
    return filename

def send_to_telegram(filename, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    with open(filename, 'rb') as v:
        requests.post(url, data={'chat_id': TELEGRAM_CHAT_ID, 'caption': caption}, files={'video': v})

if __name__ == "__main__":
    target_url = get_next_video()
    if target_url:
        video_link = get_video_link_via_browser(target_url)
        if video_link:
            file = download_video(video_link)
            # Hindi translation logic yahan add kar sakte hain
            send_to_telegram(file, "New Reel Downloaded ✨")
            with open(HISTORY_FILE, 'a') as h: h.write(target_url + "\n")
            os.remove(file)
            print("🎉 Done!")
        else:
            print("❌ Could not extract video link.")
