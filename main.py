import os
import requests

# GitHub Secrets
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

VIDEO_DIR = "videos"

def upload_to_catbox(file_path):
    url = "https://catbox.moe/user/api.php"
    data = {"reqtype": "fileupload"}
    with open(file_path, "rb") as f:
        files = {"fileToUpload": f}
        response = requests.post(url, data=data, files=files)
    return response.text

def main():
    if not os.path.exists(VIDEO_DIR):
        print("Folder nahi mila")
        return

    # फोल्डर के अंदर से फाइल्स की लिस्ट लेना
    video_files = sorted([f for f in os.listdir(VIDEO_DIR) if f.lower().endswith(('.mp4', '.mkv', '.mov'))])
    
    if not video_files:
        print("Koi video bacha nahi hai")
        return

    # सिर्फ पहली वीडियो फाइल चुनना
    video_to_upload = video_files[0]
    file_path = os.path.join(VIDEO_DIR, video_to_upload)

    try:
        # Catbox पर अपलोड
        catbox_link = upload_to_catbox(file_path)
        
        # SEO Hashtags
        seo_hashtags = "#trending #viral #foryou #explore #instagram #reels #video #tiktok #fyp"

        # आपका पसंदीदा फॉर्मेट
        caption = (
            f"Content\n"
            f"New video uploaded successfully\n"
            f".\n"
            f".\n"
            f".\n"
            f".\n"
            f".\n"
            f".\n"
            f"{seo_hashtags}\n\n"
            f"Watch here: {catbox_link}"
        )

        # Telegram Send
        if BOT_TOKEN and CHAT_ID:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": caption})

        # Webhook Send
        if WEBHOOK_URL:
            requests.post(WEBHOOK_URL, json={"content": caption})

        # सिर्फ उस एक फाइल को डिलीट करना (पूरा फोल्डर नहीं)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Success: {video_to_upload} delete ho gayi hai.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
