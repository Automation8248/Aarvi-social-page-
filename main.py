import os
import requests

# आपके GitHub Secrets के नाम
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
        print("Videos folder nahi mila")
        return

    # फोल्डर से वीडियो फाइल ढूंढना
    video_files = [f for f in os.listdir(VIDEO_DIR) if f.lower().endswith(('.mp4', '.mkv', '.mov'))]
    
    if not video_files:
        print("Koi video nahi bacha hai")
        return

    # पहली वीडियो फाइल चुनें
    video_to_upload = video_files[0]
    file_path = os.path.join(VIDEO_DIR, video_to_upload)

    try:
        # Catbox पर अपलोड
        catbox_link = upload_to_catbox(file_path)
        
        # सादा कैप्शन (बिना # और बिना *)
        caption = f"New Trending Video \n\nDirect Link: {catbox_link} \n\nDaily Video Update"

        # Telegram पर भेजना
        if BOT_TOKEN and CHAT_ID:
            tg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            requests.post(tg_url, json={"chat_id": CHAT_ID, "text": caption})

        # Webhook पर भेजना
        if WEBHOOK_URL:
            requests.post(WEBHOOK_URL, json={"content": caption})

        # फाइल डिलीट करना
        os.remove(file_path)
        print(f"Post ho gaya aur {video_to_upload} delete kar di gayi")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
