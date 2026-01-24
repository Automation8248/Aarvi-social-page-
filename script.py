import os
import instaloader
import requests
import shutil

# Configurations
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"]

LINKS_FILE = "links.txt"
HISTORY_FILE = "history.txt"

def get_next_link():
    # History check karna
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            history = set(line.strip() for line in f)
    else:
        history = set()

    # Pehla naya link dhundna
    with open(LINKS_FILE, "r") as f:
        for line in f:
            link = line.strip()
            if link and link not in history:
                return link
    return None

def download_video(link):
    print("Downloading from Instagram...")
    L = instaloader.Instaloader()
    try:
        shortcode = link.split("/")[-2]
        post = instaloader.Post.from_shortcode(L.context, shortcode)
    except Exception as e:
        print(f"Error fetching post metadata: {e}")
        return None, None, None
    
    target_dir = "downloads"
    # Download
    L.download_post(post, target=target_dir)
    
    video_path = None
    caption = post.caption if post.caption else "No Caption"
    
    # Folder mein mp4 file dhundna
    for file in os.listdir(target_dir):
        if file.endswith(".mp4"):
            video_path = os.path.join(target_dir, file)
            break
            
    return video_path, caption, shortcode

def upload_to_catbox(file_path):
    print("Uploading to Catbox.moe...")
    url = "https://catbox.moe/user/api.php"
    try:
        with open(file_path, "rb") as f:
            payload = {
                "reqtype": "fileupload",
                "userhash": "" # Optional: Agar account hai to yahan hash dalein
            }
            files = {
                "fileToUpload": f
            }
            response = requests.post(url, data=payload, files=files)
            
            if response.status_code == 200:
                catbox_url = response.text.strip()
                print(f"Uploaded Successfully: {catbox_url}")
                return catbox_url
            else:
                print(f"Catbox Error: {response.text}")
                return None
    except Exception as e:
        print(f"Upload Exception: {e}")
        return None

def post_to_telegram(catbox_link, caption):
    # Telegram URL method se video bhejega (fast)
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID, 
        'video': catbox_link, 
        'caption': caption
    }
    requests.post(url, data=payload)

def trigger_webhook(original_link, catbox_link, caption):
    data = {
        "original_instagram_link": original_link,
        "video_direct_url": catbox_link,
        "caption": caption,
        "status": "processed"
    }
    # Webhook par JSON data bhejna
    requests.post(WEBHOOK_URL, json=data)

def update_history(link):
    with open(HISTORY_FILE, "a") as f:
        f.write(f"{link}\n")

if __name__ == "__main__":
    link = get_next_link()
    
    if link:
        print(f"Processing: {link}")
        
        # 1. Download Video
        video_path, caption, shortcode = download_video(link)
        
        if video_path:
            # 2. Upload to Catbox
            catbox_url = upload_to_catbox(video_path)
            
            if catbox_url:
                print("Posting to Telegram via Catbox Link...")
                # 3. Post to Telegram
                post_to_telegram(catbox_url, caption)
                
                print("Triggering Webhook...")
                # 4. Webhook Trigger
                trigger_webhook(link, catbox_url, caption)
                
                print("Updating History...")
                update_history(link)
            else:
                print("Catbox upload failed. Skipping post.")
            
            # Cleanup
            if os.path.exists("downloads"):
                shutil.rmtree("downloads")
        else:
            print("Video download failed or file not found.")
    else:
        print("No new links to process today.")
