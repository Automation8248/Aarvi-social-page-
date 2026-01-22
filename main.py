import os
import requests
import yt_dlp
from urllib.parse import urlparse, unquote

# --- Secrets Check (Logs me dikhega ki secrets mile ya nahi) ---
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

print("--- DEBUG INFO ---")
print(f"Telegram Token Found: {'YES' if TELEGRAM_BOT_TOKEN else 'NO'}")
print(f"Chat ID Found: {'YES' if TELEGRAM_CHAT_ID else 'NO'}")
print(f"Webhook URL Found: {'YES' if WEBHOOK_URL else 'NO'}")
print("------------------")

FILES_DIR = "downloads"
LINKS_FILE = 'link.txt'
HISTORY_FILE = 'history.txt'

def get_filename_from_url(url):
    path = urlparse(url).path
    filename = unquote(os.path.basename(path))
    if not filename:
        return "Unknown_Video"
    return filename

def download_video(url):
    if not os.path.exists(FILES_DIR):
        os.makedirs(FILES_DIR)

    ydl_opts = {
        'format': 'best',
        'outtmpl': f'{FILES_DIR}/%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'restrictfilenames': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Attempting to download: {url}")
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            title = info.get('title')
            
            if not title or title.startswith('http'):
                title = get_filename_from_url(url)
                
            return filename, title
            
    except Exception as e:
        print(f"❌ Download Error: {e}")
        return None, None

def upload_to_catbox(file_path):
    url = "https://catbox.moe/user/api.php"
    try:
        print(f"Uploading file size: {os.path.getsize(file_path) / (1024*1024):.2f} MB")
        with open(file_path, 'rb') as f:
            data = {'reqtype': 'fileupload', 'userhash': ''}
            files = {'fileToUpload': f}
            response = requests.post(url, data=data, files=files)
            
        if response.status_code == 200:
            return response.text
        else:
            print(f"❌ Catbox Upload Failed. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Upload Exception: {e}")
        return None

def send_notification(catbox_link, title):
    caption = f"🎬 **{title}**\n\n🔗 **Download:** {catbox_link}"
    
    # 1. Telegram Debugging
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        try:
            resp = requests.post(tg_url, json={
                'chat_id': TELEGRAM_CHAT_ID, 
                'text': caption, 
                'parse_mode': 'Markdown'
            })
            if resp.status_code == 200:
                print("✅ Telegram Message Sent!")
            else:
                print(f"❌ Telegram Fail: {resp.text}")
        except Exception as e:
            print(f"❌ Telegram Error: {e}")
    else:
        print("⚠️ Skipping Telegram: Token or Chat ID missing.")

    # 2. Webhook Debugging
    if WEBHOOK_URL:
        try:
            resp = requests.post(WEBHOOK_URL, json={
                'video_url': catbox_link, 
                'title': title,
                'caption': caption
            })
            print(f"✅ Webhook Status: {resp.status_code}")
        except Exception as e:
            print(f"❌ Webhook Error: {e}")
    else:
        print("⚠️ Skipping Webhook: URL missing.")

def main():
    if not os.path.exists(HISTORY_FILE):
        open(HISTORY_FILE, 'w').close()
    
    with open(HISTORY_FILE, 'r') as f:
        history = f.read().splitlines()

    if not os.path.exists(LINKS_FILE):
        print("Link file not found!")
        return

    with open(LINKS_FILE, 'r') as f:
        links = [line.strip() for line in f if line.strip()]

    if not links:
        print("No links found in link.txt")

    for link in links:
        if link in history:
            print(f"Skipping (History match): {link}")
            continue
        
        print(f"Processing: {link}")
        
        file_path, title = download_video(link)
        
        if file_path and os.path.exists(file_path):
            print(f"Downloaded successfully: {title}")
            
            catbox_url = upload_to_catbox(file_path)
            
            if catbox_url:
                print(f"Catbox URL Generated: {catbox_url}")
                send_notification(catbox_url, title)
                
                with open(HISTORY_FILE, 'a') as f:
                    f.write(link + '\n')
            else:
                print("❌ Upload failed, notification skipped.")
            
            os.remove(file_path)
        else:
            print("❌ Download Failed.")

if __name__ == "__main__":
    main()
