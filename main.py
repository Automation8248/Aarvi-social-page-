import os
import requests

# GitHub Secrets
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

VIDEO_DIR = "videos"

def main():
    if not os.path.exists(VIDEO_DIR):
        print("Folder nahi mila")
        return

    # फोल्डर के अंदर से फाइल्स की लिस्ट (Alphabetical order में)
    video_files = sorted([f for f in os.listdir(VIDEO_DIR) if f.lower().endswith(('.mp4', '.mkv', '.mov'))])
    
    if not video_files:
        print("Koi video bacha nahi hai")
        return

    # सिर्फ पहली वीडियो फाइल (Content)
    video_to_process = video_files[0]
    file_path = os.path.join(VIDEO_DIR, video_to_process)

    try:
        # SEO Hashtags
        seo_hashtags = "#trending #viral #foryou #explore #instagram #reels #video #tiktok #fyp"

        # आपका सटीक फॉर्मेट
        caption_text = (
            f"New video post\n"
            f".\n"
            f".\n"
            f".\n"
            f".\n"
            f".\n"
            f"{seo_hashtags}"
        )

        # 1. Telegram पर सीधा वीडियो भेजना
        if BOT_TOKEN and CHAT_ID:
            tg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
            with open(file_path, "rb") as video:
                requests.post(tg_url, files={"video": video}, data={"chat_id": CHAT_ID, "caption": caption_text})

        # 2. Webhook पर भेजना
        if WEBHOOK_URL:
            requests.post(WEBHOOK_URL, json={"content": caption_text})

        # 3. सिर्फ इस्तेमाल हुई फ़ाइल को डिलीट करना
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Success: Only {video_to_process} has been deleted.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
