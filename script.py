import os
import requests
import shutil
import time

# Configurations
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"]

LINKS_FILE = "links.txt"
HISTORY_FILE = "history.txt"

# Cobalt API Instance (Ye video download handle karega)
COBALT_API_URL = "https://api.cobalt.tools/api/json"

def get_next_link():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            history = set(line.strip() for line in f)
    else:
        history = set()

    with open(LINKS_FILE, "r") as f:
        for line in f:
            link = line.strip()
            if link and link not in history:
                return link
    return None

def download_via_cobalt(link):
    print(f"Requesting Cobalt API for: {link}")
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "url": link,
        "vCodec": "h264",
        "vQuality": "720",
        "filenamePattern": "basic"
    }

    try:
        response = requests.post(COBALT_API_URL, json=payload, headers=headers)
        data = response.json()
        
        if "url" in data:
            video_url = data["url"]
            print("Video URL found via Cobalt.")
            
            # Ab video ko download karte hain
            if not os.path.exists("downloads"):
                os.makedirs("downloads")
            
            video_path = "downloads/video.mp4"
            
            # Stream download to avoid memory issues
            with requests.get(video_url, stream=True) as r:
                r.raise_for_status()
                with open(video_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            return video_path
        else:
            print(f"Cobalt API Error: {data}")
            return None
            
    except Exception as e:
        print(f"Error connecting to Cobalt: {e}")
        return None

def upload_to_catbox(file_path):
    print("Uploading to Catbox.moe...")
    url = "https://catbox.moe/user/api.php"
    try:
        with open(file_path, "rb") as f:
            payload = {"reqtype": "fileupload"}
            files = {"fileToUpload": f}
            response = requests.post(url, data=payload, files=files)
            
            if response.status_code == 200:
                return response.text.strip()
            else:
                print(f"Catbox Error: {response.text}")
                return None
    except Exception as e:
        print(f"Upload Exception: {e}")
        return None

def post_to_telegram(catbox_link, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID, 
        'video': catbox_link, 
        'caption': caption
    }
    requests.post(url, data=payload)

def trigger_webhook(original_link, catbox_link, caption):
    data = {
        "original_link": original_link,
        "catbox_url": catbox_link,
        "caption": caption
    }
    requests.post(WEBHOOK_URL, json=data)

def update_history(link):
    with open(HISTORY_FILE, "a") as f:
        f.write(f"{link}\n")

if __name__ == "__main__":
    link = get_next_link()
    
    if link:
        print(f"Processing: {link}")
        
        # Note: IP blocks ki wajah se caption extract karna mushkil hai.
        # Hum generic caption use karenge ya user manual link mein provide kar sakta hai.
        caption = f"New Reel! 🔥\n\nSource: {link}"
        
        # 1. Download via API (Bypasses IP Block)
        video_path = download_via_cobalt(link)
        
        if video_path:
            # 2. Upload to Catbox
            catbox_url = upload_to_catbox(video_path)
            
            if catbox_url:
                print(f"Catbox Link: {catbox_url}")
                
                # 3. Post to Telegram
                post_to_telegram(catbox_url, caption)
                
                # 4. Webhook
                trigger_webhook(link, catbox_url, caption)
                
                # 5. Save History
                update_history(link)
                
                # Cleanup
                shutil.rmtree("downloads")
            else:
                print("Failed to upload to Catbox.")
        else:
            print("Failed to download video via API.")
    else:
        print("No new links found.")    if link:
        print(f"Processing: {link}")
        
        # 1. Download
        video_path, caption = download_video(link)
        
        if video_path:
            # 2. Upload to Catbox
            catbox_url = upload_to_catbox(video_path)
            
            if catbox_url:
                print("Posting to Telegram...")
                # 3. Post
                post_to_telegram(catbox_url, caption)
                
                print("Triggering Webhook...")
                # 4. Webhook
                trigger_webhook(link, catbox_url, caption)
                
                print("Updating History...")
                update_history(link)
            else:
                print("Catbox upload failed.")
            
            # Cleanup
            if os.path.exists("downloads"):
                shutil.rmtree("downloads")
        else:
            print("Video download failed.")
    else:
        print("No new links to process today.")
