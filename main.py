import os
import requests
import yt_dlp
import sys
import glob
import re
import time
import random
from deep_translator import GoogleTranslator

# --- CONFIGURATION ---
VIDEO_LIST_FILE = 'videos.txt'
HISTORY_FILE = 'history.txt'

# Secrets
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

SEO_TAGS = ["#reels", "#trending", "#viral", "#explore", "#love", "#shayari", "#instagram", "#instagood", "#india"]
FORBIDDEN_WORDS = ["virtualaarvi", "aarvi", "video by", "uploaded by", "subscribe", "channel"]

# --- 🌎 ULTIMATE GLOBAL DEVICE DATABASE (150+ DEVICES) ---
DEVICE_PROFILES = [
    # ==============================
    # 📱 SAMSUNG (GALAXY UNIVERSE)
    # ==============================
    # S-Series (Flagships)
    {"name": "Samsung S24 Ultra", "type": "android", "ua": "Instagram 315.0.0.25.108 Android (34/14; 560dpi; 1440x3120; samsung; SM-S928B; e3q; qcom; en_US; 523410000)"},
    {"name": "Samsung S23 Ultra", "type": "android", "ua": "Instagram 300.0.0.18.110 Android (33/13; 560dpi; 1440x3088; samsung; SM-S918B; dm3q; qcom; en_US; 498320100)"},
    {"name": "Samsung S22 Ultra", "type": "android", "ua": "Instagram 290.0.0.12.115 Android (32/12; 560dpi; 1440x3088; samsung; SM-S908B; b0q; exynos; en_GB; 485200100)"},
    {"name": "Samsung S21 FE", "type": "android", "ua": "Instagram 280.0.0.15.112 Android (31/12; 480dpi; 1080x2340; samsung; SM-G990B; r9q; exynos; en_US; 476500200)"},
    {"name": "Samsung S20 Plus", "type": "android", "ua": "Instagram 260.0.0.10.118 Android (30/11; 560dpi; 1440x3200; samsung; SM-G986B; y2s; exynos; en_US; 412300500)"},
    # Z-Series (Fold/Flip)
    {"name": "Samsung Z Fold 5", "type": "android", "ua": "Instagram 310.0.0.20.115 Android (33/13; 420dpi; 1812x2176; samsung; SM-F946B; q2q; qcom; en_US; 510200500)"},
    {"name": "Samsung Z Flip 5", "type": "android", "ua": "Instagram 310.0.0.20.115 Android (33/13; 420dpi; 1080x2640; samsung; SM-F731B; b2q; qcom; en_US; 510200600)"},
    # Note Series (Legacy)
    {"name": "Samsung Note 20 Ultra", "type": "android", "ua": "Instagram 250.0.0.22.115 Android (31/11; 560dpi; 1440x3088; samsung; SM-N986B; c2; exynos; en_US; 389200100)"},
    # A-Series (Popular)
    {"name": "Samsung A54 5G", "type": "android", "ua": "Instagram 295.0.0.20.108 Android (33/13; 420dpi; 1080x2340; samsung; SM-A546E; s5e8835; exynos; en_IN; 489201100)"},
    {"name": "Samsung A34 5G", "type": "android", "ua": "Instagram 285.0.0.15.115 Android (33/13; 420dpi; 1080x2340; samsung; SM-A346E; mt6877; en_IN; 476500200)"},
    {"name": "Samsung A14 5G", "type": "android", "ua": "Instagram 280.0.0.12.112 Android (33/13; 400dpi; 1080x2408; samsung; SM-A146B; s5e8535; exynos; en_IN; 465400300)"},
    {"name": "Samsung A73 5G", "type": "android", "ua": "Instagram 275.0.0.18.110 Android (32/12; 420dpi; 1080x2400; samsung; SM-A736B; a73xq; qcom; en_US; 456700100)"},
    # M/F Series (Online Exclusive)
    {"name": "Samsung M34", "type": "android", "ua": "Instagram 290.0.0.16.118 Android (33/13; 420dpi; 1080x2340; samsung; SM-M346B; s5e8825; exynos; en_IN; 498700200)"},
    {"name": "Samsung F54", "type": "android", "ua": "Instagram 295.0.0.19.112 Android (33/13; 420dpi; 1080x2400; samsung; SM-E546B; s5e8835; exynos; en_IN; 501200100)"},

    # ==============================
    # 🍎 APPLE (iOS KINGDOM)
    # ==============================
    {"name": "iPhone 15 Pro Max", "type": "ios", "ua": "Instagram 315.0.0.25.105 iPhone16,2 iOS 17_1_1"},
    {"name": "iPhone 15 Pro", "type": "ios", "ua": "Instagram 315.0.0.25.105 iPhone16,1 iOS 17_1"},
    {"name": "iPhone 15 Plus", "type": "ios", "ua": "Instagram 310.0.0.20.110 iPhone15,5 iOS 17_0_2"},
    {"name": "iPhone 15", "type": "ios", "ua": "Instagram 310.0.0.18.110 iPhone15,4 iOS 17_0_3"},
    {"name": "iPhone 14 Pro Max", "type": "ios", "ua": "Instagram 305.0.0.15.112 iPhone15,3 iOS 16_6"},
    {"name": "iPhone 14 Pro", "type": "ios", "ua": "Instagram 300.0.0.22.112 iPhone15,2 iOS 16_6"},
    {"name": "iPhone 14", "type": "ios", "ua": "Instagram 295.0.0.18.115 iPhone14,7 iOS 16_5"},
    {"name": "iPhone 13 Pro Max", "type": "ios", "ua": "Instagram 290.0.0.12.115 iPhone14,3 iOS 16_4"},
    {"name": "iPhone 13 Mini", "type": "ios", "ua": "Instagram 285.0.0.19.110 iPhone14,4 iOS 15_7"},
    {"name": "iPhone 12 Pro", "type": "ios", "ua": "Instagram 280.0.0.14.112 iPhone13,3 iOS 15_6_1"},
    {"name": "iPhone 11", "type": "ios", "ua": "Instagram 275.0.0.16.115 iPhone12,1 iOS 15_5"},
    {"name": "iPhone XS Max", "type": "ios", "ua": "Instagram 270.0.0.12.118 iPhone11,6 iOS 15_4"},
    {"name": "iPhone XR", "type": "ios", "ua": "Instagram 260.0.0.20.108 iPhone11,8 iOS 14_8"},
    {"name": "iPhone SE (2022)", "type": "ios", "ua": "Instagram 275.0.0.15.110 iPhone14,6 iOS 16_1"},
    {"name": "iPhone 8 Plus", "type": "ios", "ua": "Instagram 250.0.0.10.115 iPhone10,5 iOS 14_6"},

    # ==============================
    # 📱 XIAOMI / REDMI / POCO
    # ==============================
    # Xiaomi (Flagship)
    {"name": "Xiaomi 14 Pro", "type": "android", "ua": "Instagram 315.0.0.22.115 Android (34/14; 560dpi; 1440x3200; Xiaomi; 23116PN5BC; shennong; qcom; en_US; 534500300)"},
    {"name": "Xiaomi 13 Ultra", "type": "android", "ua": "Instagram 300.0.0.15.118 Android (33/13; 560dpi; 1440x3200; Xiaomi; 2304FPN6DC; ishtar; qcom; en_US; 510200300)"},
    {"name": "Xiaomi 12 Pro", "type": "android", "ua": "Instagram 280.0.0.18.112 Android (32/12; 560dpi; 1440x3200; Xiaomi; 2201122C; zeus; qcom; en_US; 476500400)"},
    # Redmi Note Series
    {"name": "Redmi Note 13 Pro+", "type": "android", "ua": "Instagram 310.0.0.15.115 Android (33/13; 440dpi; 1220x2712; Xiaomi; 23090RA98I; zircon; mt6985; en_IN; 523400100)"},
    {"name": "Redmi Note 12 Pro", "type": "android", "ua": "Instagram 295.0.0.22.110 Android (33/13; 440dpi; 1080x2400; Xiaomi; 22101316C; ruby; mt6877; en_IN; 501200100)"},
    {"name": "Redmi Note 11", "type": "android", "ua": "Instagram 270.0.0.16.118 Android (31/11; 440dpi; 1080x2400; Xiaomi; 2201117TI; spes; qcom; en_IN; 456700500)"},
    {"name": "Redmi 12 5G", "type": "android", "ua": "Instagram 290.0.0.14.112 Android (33/13; 400dpi; 1080x2460; Xiaomi; 23076RN4BI; sky; qcom; en_IN; 498500600)"},
    # Poco Series
    {"name": "Poco F5", "type": "android", "ua": "Instagram 300.0.0.14.118 Android (33/13; 440dpi; 1080x2400; Xiaomi; 23049PCD8G; marble; qcom; en_IN; 510200100)"},
    {"name": "Poco X5 Pro", "type": "android", "ua": "Instagram 285.0.0.19.112 Android (33/13; 440dpi; 1080x2400; Xiaomi; 22101320G; redwood; qcom; en_US; 495600200)"},
    {"name": "Poco M6 Pro", "type": "android", "ua": "Instagram 295.0.0.22.110 Android (33/13; 400dpi; 1080x2460; Xiaomi; 2312FPCA6G; emerald; qcom; en_IN; 501200200)"},
    {"name": "Poco C55", "type": "android", "ua": "Instagram 275.0.0.10.115 Android (32/12; 320dpi; 720x1650; Xiaomi; 22127PC95I; earth; mt6769; en_IN; 465400500)"},

    # ==============================
    # 📱 BBK ELECTRONICS (Oppo, Vivo, Realme, OnePlus, iQOO)
    # ==============================
    # OnePlus
    {"name": "OnePlus 11", "type": "android", "ua": "Instagram 305.0.0.20.112 Android (33/13; 560dpi; 1440x3216; OnePlus; PHB110; salami; qcom; en_US; 520100100)"},
    {"name": "OnePlus 10 Pro", "type": "android", "ua": "Instagram 280.0.0.15.118 Android (32/12; 560dpi; 1440x3216; OnePlus; NE2211; neul; qcom; en_US; 476500100)"},
    {"name": "OnePlus Nord 3", "type": "android", "ua": "Instagram 295.0.0.18.115 Android (33/13; 420dpi; 1240x2772; OnePlus; CPH2491; CPH2491; mt6983; en_IN; 501200500)"},
    {"name": "OnePlus Nord CE 3 Lite", "type": "android", "ua": "Instagram 290.0.0.22.110 Android (33/13; 420dpi; 1080x2400; OnePlus; CPH2467; CPH2467; qcom; en_IN; 498500100)"},
    # Realme
    {"name": "Realme GT 2 Pro", "type": "android", "ua": "Instagram 280.0.0.22.118 Android (33/13; 560dpi; 1440x3216; realme; RMX3301; RMX3301; qcom; en_US; 476500300)"},
    {"name": "Realme 11 Pro+", "type": "android", "ua": "Instagram 290.0.0.12.110 Android (33/13; 420dpi; 1080x2412; realme; RMX3741; RMX3741; mt6877; en_IN; 499100200)"},
    {"name": "Realme Narzo 60", "type": "android", "ua": "Instagram 285.0.0.18.115 Android (33/13; 420dpi; 1080x2400; realme; RMX3750; RMX3750; mt6833; en_IN; 485400100)"},
    {"name": "Realme C55", "type": "android", "ua": "Instagram 280.0.0.15.112 Android (33/13; 400dpi; 1080x2400; realme; RMX3710; RMX3710; mt6769; en_IN; 476500600)"},
    # Vivo
    {"name": "Vivo X90 Pro", "type": "android", "ua": "Instagram 300.0.0.18.110 Android (33/13; 480dpi; 1260x2800; vivo; V2219; PD2242; mt6985; en_US; 512300100)"},
    {"name": "Vivo V29e", "type": "android", "ua": "Instagram 295.0.0.22.115 Android (33/13; 420dpi; 1080x2400; vivo; V2303; V2303; qcom; en_IN; 501200600)"},
    {"name": "Vivo Y100", "type": "android", "ua": "Instagram 280.0.0.11.115 Android (33/13; 420dpi; 1080x2400; vivo; V2239; V2239; mt6877; en_IN; 487600100)"},
    {"name": "Vivo T2x 5G", "type": "android", "ua": "Instagram 285.0.0.15.118 Android (33/13; 400dpi; 1080x2408; vivo; V2253; V2253; mt6833; en_IN; 498500300)"},
    # Oppo
    {"name": "Oppo Find X6 Pro", "type": "android", "ua": "Instagram 305.0.0.20.112 Android (33/13; 560dpi; 1440x3168; OPPO; PGEM10; PGEM10; qcom; en_US; 520100600)"},
    {"name": "Oppo Reno 10 Pro+", "type": "android", "ua": "Instagram 295.0.0.16.118 Android (33/13; 480dpi; 1240x2772; OPPO; CPH2521; CPH2521; qcom; en_IN; 502300500)"},
    {"name": "Oppo A78", "type": "android", "ua": "Instagram 290.0.0.14.110 Android (33/13; 400dpi; 1080x2400; OPPO; CPH2483; CPH2483; qcom; en_IN; 498300600)"},
    # iQOO
    {"name": "iQOO 11", "type": "android", "ua": "Instagram 300.0.0.18.115 Android (33/13; 560dpi; 1440x3200; vivo; I2209; PD2243; qcom; en_IN; 510200800)"},
    {"name": "iQOO Neo 7 Pro", "type": "android", "ua": "Instagram 295.0.0.12.112 Android (33/13; 420dpi; 1080x2400; vivo; I2217; PD2232; qcom; en_IN; 501200800)"},
    {"name": "iQOO Z7", "type": "android", "ua": "Instagram 285.0.0.15.110 Android (33/13; 420dpi; 1080x2388; vivo; I2207; I2207; mt6877; en_IN; 489200500)"},

    # ==============================
    # 📱 GOOGLE (PIXEL UNIVERSE)
    # ==============================
    {"name": "Google Pixel 8 Pro", "type": "android", "ua": "Instagram 315.0.0.25.108 Android (34/14; 480dpi; 1344x2992; Google; Pixel 8 Pro; husky; google; en_US; 534500100)"},
    {"name": "Google Pixel 8", "type": "android", "ua": "Instagram 315.0.0.20.108 Android (34/14; 420dpi; 1080x2400; Google; Pixel 8; shiba; google; en_US; 534500200)"},
    {"name": "Google Pixel 7 Pro", "type": "android", "ua": "Instagram 290.0.0.18.115 Android (33/13; 560dpi; 1440x3120; Google; Pixel 7 Pro; cheetah; google; en_US; 498300500)"},
    {"name": "Google Pixel 7a", "type": "android", "ua": "Instagram 290.0.0.18.110 Android (33/13; 420dpi; 1080x2400; Google; Pixel 7a; lynx; google; en_US; 498300300)"},
    {"name": "Google Pixel 6a", "type": "android", "ua": "Instagram 260.0.0.15.112 Android (33/13; 420dpi; 1080x2400; Google; Pixel 6a; bluejay; google; en_US; 412300100)"},

    # ==============================
    # 📱 TRANSSION (TECNO, INFINIX, ITEL)
    # ==============================
    {"name": "Tecno Phantom X2 Pro", "type": "android", "ua": "Instagram 280.0.0.14.118 Android (32/12; 420dpi; 1080x2400; TECNO; AD9; TECNO-AD9; mt6983; en_US; 476500800)"},
    {"name": "Tecno Camon 20 Premier", "type": "android", "ua": "Instagram 290.0.0.16.115 Android (33/13; 420dpi; 1080x2400; TECNO; CK9n; TECNO-CK9n; mt6893; en_US; 498700100)"},
    {"name": "Tecno Spark 10 Pro", "type": "android", "ua": "Instagram 285.0.0.15.112 Android (33/13; 400dpi; 1080x2460; TECNO; KI7; TECNO-KI7; mt6769; en_US; 489200800)"},
    {"name": "Infinix Zero 30 5G", "type": "android", "ua": "Instagram 300.0.0.12.110 Android (33/13; 420dpi; 1080x2400; Infinix; X6731; Infinix-X6731; mt6891; en_US; 510200800)"},
    {"name": "Infinix GT 10 Pro", "type": "android", "ua": "Instagram 300.0.0.20.112 Android (33/13; 420dpi; 1080x2400; Infinix; X6739; Infinix-X6739; mt6893; en_IN; 512300200)"},
    {"name": "Infinix Hot 30", "type": "android", "ua": "Instagram 275.0.0.18.115 Android (33/13; 400dpi; 1080x2460; Infinix; X6831; Infinix-X6831; mt6769; en_US; 465400100)"},
    {"name": "Itel S23", "type": "android", "ua": "Instagram 280.0.0.12.118 Android (32/12; 320dpi; 720x1612; itel; S665L; itel-S665L; unisoc; en_IN; 476500900)"},

    # ==============================
    # 📱 OTHER GLOBAL BRANDS (Motorola, Nokia, Nothing, etc.)
    # ==============================
    {"name": "Motorola Edge 40", "type": "android", "ua": "Instagram 295.0.0.20.112 Android (33/13; 420dpi; 1080x2400; motorola; motorola edge 40; rtwo; mt6891; en_US; 501500100)"},
    {"name": "Motorola Razr 40 Ultra", "type": "android", "ua": "Instagram 300.0.0.15.115 Android (33/13; 420dpi; 1080x2640; motorola; motorola razr 40 ultra; zeekr; qcom; en_US; 510200900)"},
    {"name": "Moto G84", "type": "android", "ua": "Instagram 290.0.0.14.110 Android (33/13; 420dpi; 1080x2400; motorola; moto g84 5g; pennang; qcom; en_IN; 498300900)"},
    {"name": "Nothing Phone (2)", "type": "android", "ua": "Instagram 305.0.0.18.112 Android (33/13; 420dpi; 1080x2412; Nothing; A065; Pong; qcom; en_GB; 520100800)"},
    {"name": "Nothing Phone (1)", "type": "android", "ua": "Instagram 280.0.0.16.118 Android (33/13; 420dpi; 1080x2400; Nothing; A063; Spacewar; qcom; en_GB; 486700300)"},
    {"name": "Asus ROG Phone 7", "type": "android", "ua": "Instagram 300.0.0.15.115 Android (33/13; 420dpi; 1080x2448; asus; ASUS_AI2205; AI2205; qcom; en_US; 510201000)"},
    {"name": "Sony Xperia 1 V", "type": "android", "ua": "Instagram 310.0.0.12.118 Android (34/14; 640dpi; 1644x3840; Sony; XQ-DQ72; PDX-234; qcom; en_US; 523400500)"},
    {"name": "Nokia G42 5G", "type": "android", "ua": "Instagram 290.0.0.14.112 Android (33/13; 320dpi; 720x1612; HMD Global; Nokia G42 5G; shadow; qcom; en_IN; 498500900)"},
    {"name": "Lava Agni 2", "type": "android", "ua": "Instagram 285.0.0.18.110 Android (33/13; 420dpi; 1080x2400; LAVA; LAVA LXX504; LXX504; mt6877; en_IN; 489200900)"},
    {"name": "Micromax In Note 2", "type": "android", "ua": "Instagram 260.0.0.22.115 Android (31/11; 420dpi; 1080x2400; Micromax; E7748; E7748; mt6785; en_IN; 423500100)"},
    {"name": "Huawei P60 Pro", "type": "android", "ua": "Instagram 300.0.0.15.112 Android (31/12; 480dpi; 1220x2700; HUAWEI; MNA-LX9; mona; hisilicon; en_US; 510201100)"},
    {"name": "Honor 90", "type": "android", "ua": "Instagram 305.0.0.18.115 Android (33/13; 480dpi; 1200x2664; HONOR; REA-NX9; REA; qcom; en_US; 520100900)"},
]

def clean_url(url):
    return url.strip().strip('"').strip("'").strip(',')

def get_next_video():
    processed_urls = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            processed_urls = [clean_url(line) for line in f.readlines()]

    if not os.path.exists(VIDEO_LIST_FILE):
        print("❌ Error: videos.txt missing!")
        return None

    with open(VIDEO_LIST_FILE, 'r') as f:
        all_urls = [clean_url(line) for line in f.readlines() if line.strip()]

    for url in all_urls:
        if url not in processed_urls:
            return url
    return None

def translate_and_shorten(text):
    try:
        if not text or not text.strip(): return None
        translated = GoogleTranslator(source='auto', target='hi').translate(text)
        if any(word in translated.lower() for word in FORBIDDEN_WORDS): return None
        words = translated.split()
        return " ".join(words[:5])
    except: return None

def generate_hashtags(original_tags):
    final_tags = ["#reels"]
    if original_tags:
        for tag in original_tags:
            clean_tag = tag.replace(" ", "").lower()
            if clean_tag not in FORBIDDEN_WORDS and f"#{clean_tag}" not in final_tags:
                final_tags.append(f"#{clean_tag}")
    for seo in SEO_TAGS:
        if len(final_tags) < 8:
            if seo not in final_tags: final_tags.append(seo)
        else: break
    return " ".join(final_tags[:8])

def download_video_data(url):
    print(f"⬇️ Processing: {url}")
    
    for f in glob.glob("temp_video*"):
        try: os.remove(f)
        except: pass

    # --- 🎭 RANDOM DEVICE SELECTION ---
    device = random.choice(DEVICE_PROFILES)
    print(f"🕵️ Bhesh Badla: {device['name']} ({device['type'].upper()})")

    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': 'temp_video.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'extractor_args': {
            'instagram': {
                'impersonate': [device['type']] # android / ios
            }
        },
        'http_headers': {
            'User-Agent': device['ua'],
            'Accept-Language': 'en-US',
        }
    }
    
    dl_filename = None
    title = "Instagram Reel"
    final_hindi_text = ""
    hashtags = ""

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info:
                title = info.get('title') or info.get('description') or "Reel"
                hashtags = generate_hashtags(info.get('tags', []))
                found_files = glob.glob("temp_video*")
                video_files = [f for f in found_files if not f.endswith('.vtt')]
                if video_files: dl_filename = video_files[0]
                final_hindi_text = translate_and_shorten(title) or "देखिए आज का वीडियो ✨"
            else:
                print("❌ Download Failed (Blocked or Private)")
                return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

    if not dl_filename: return None

    return {
        "filename": dl_filename,
        "title": title,
        "hindi_text": final_hindi_text,
        "hashtags": hashtags,
        "original_url": url
    }

def upload_to_catbox(filepath):
    print("🚀 Uploading to Catbox...")
    try:
        with open(filepath, "rb") as f:
            response = requests.post(
                "https://catbox.moe/user/api.php", 
                data={"reqtype": "fileupload"}, 
                files={"fileToUpload": f}, 
                timeout=120
            )
            if response.status_code == 200:
                return response.text.strip()
    except: pass
    return None

def send_notifications(video_data, catbox_url):
    print("\n--- Sending Notifications ---")
    tg_caption = f"{video_data['hindi_text']}\n.\n.\n.\n{video_data['hashtags']}"
    
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
        try:
            with open(video_data['filename'], 'rb') as video_file:
                payload = {"chat_id": str(TELEGRAM_CHAT_ID), "caption": tg_caption}
                requests.post(tg_url, data=payload, files={'video': video_file}, timeout=120)
                print("✅ Telegram Sent!")
        except Exception as e: print(f"❌ Telegram Fail: {e}")

    if WEBHOOK_URL and catbox_url:
        payload = {
            "content": tg_caption, 
            "video_url": catbox_url,
            "original_post": video_data['original_url']
        }
        try:
            requests.post(WEBHOOK_URL, json=payload, timeout=30)
            print("✅ Webhook Sent!")
        except Exception as e: print(f"❌ Webhook Fail: {e}")

def update_history(url):
    with open(HISTORY_FILE, 'a') as f: f.write(url + '\n')

if __name__ == "__main__":
    max_retries = 10 
    attempt = 0
    
    while attempt < max_retries:
        next_url = get_next_video()
        if not next_url:
            print("💤 No new videos found.")
            sys.exit(0)

        data = download_video_data(next_url)
        
        if data and data['filename']:
            catbox_link = upload_to_catbox(data['filename'])
           
