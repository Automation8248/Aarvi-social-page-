import os
import requests
import yt_dlp
from urllib.parse import urlparse, unquote

# --- Configuration ---
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

FILES_DIR = "downloads"
LINKS_FILE = 'link.txt'
HISTORY_FILE = 'history.txt'

def get_filename_from_url(url):
    """Fallback: Agar yt-dlp title na de paye to URL se filename nikalna"""
    path = urlparse(url).path
    filename = unquote(os.path.basename(path))
    if not filename:
        return "Unknown_Video"
    return filename

def download_video(url):
    """Direct Download Link se video download aur Title extract karta hai"""
    # Folder create karein agar nahi hai
    if not os.path.exists(FILES_DIR):
        os.makedirs(FILES_DIR)

    # yt-dlp options for direct links
    ydl_opts = {
        'format': 'best',
        'outtmpl': f'{FILES_DIR}/%(title)s.%(ext)s', # Original filename use karega
        'quiet': True,
        'no_warnings': True,
        'restrictfilenames': True, # Special characters hatane ke liye
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Metadata extract karein (Title nikalne ke liye)
            info = ydl.extract_info(url, download=True)
            
            # File path aur Title nikalein
            filename = ydl.prepare_filename(info)
            
            # Agar direct file hai to title filename hi hota hai usually
            title = info.get('title')
            
            # Agar title empty hai ya URL jaisa dikh raha hai, to URL se filename nikalo
            if not title or title.startswith('http'):
                title = get_filename_from_url(url)
                
            return filename, title
            
    except Exception as e:
        print(f"yt-dlp failed, trying fallback method: {e}")
        return None, None

def upload_to_catbox(file_path):
    """Catbox.moe par upload karta hai"""
    url = "https://catbox.moe/user/api.php"
    try:
        with open(file_path, 'rb') as f:
            data = {'reqtype': 'fileupload', 'userhash': ''}
            files = {'fileToUpload': f}
            print("Uploading to Catbox...")
            response = requests.post(url, data=data, files=files)
            
        if response.status_code == 200:
            return response.text
        else:
            print(f"Catbox Error: {response.text}")
            return None
    except Exception as e:
        print(f"Upload Error: {e}")
        return None

def send_notification(catbox_link, title):
    """Telegram aur Webhook par same Title/Caption ke sath bhejta hai"""
    
    # Caption wahi hoga jo video ka title/filename tha
    caption = f"🎬 **{title}**\n\n🔗 **Download:** {catbox_link}"
    
    # 1. Telegram
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(tg_url, json={
            'chat_id': TELEGRAM_CHAT_ID, 
            'text': caption, 
            'parse_mode': 'Markdown'
        })
        print("Telegram Notification Sent.")

    # 2. Webhook
    if WEBHOOK_URL:
        requests.post(WEBHOOK_URL, json={
            'video_url': catbox_link, 
            'title': title,
            'caption': caption
        })
        print("Webhook Notification Sent.")

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

    for link in links:
        if link in history:
            print(f"Skipping: {link}")
            continue
        
        print(f"Processing Direct Link: {link}")
        
        # Step 1: Download
        file_path, title = download_video(link)
        
        if file_path and os.path.exists(file_path):
            print(f"Downloaded: {title}")
            
            # Step 2: Upload
            catbox_url = upload_to_catbox(file_path)
            
            if catbox_url:
                print(f"Catbox Link: {catbox_url}")
                
                # Step 3: Notify (Same Title/Caption)
                send_notification(catbox_url, title)
                
                # Update History
                with open(HISTORY_FILE, 'a') as f:
                    f.write(link + '\n')
            
            # Cleanup
            os.remove(file_path)
        else:
            print("Download Failed.")

if __name__ == "__main__":
    main()
