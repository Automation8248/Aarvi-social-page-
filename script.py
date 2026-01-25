import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import os
import requests
import re

# --- CONFIGURATION ---
LINKS_FILE = "links.txt"
HISTORY_FILE = "history.txt"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# --- SEO HASHTAGS ---
SEO_HASHTAGS = "#trending #viral #instagram #reels #explore #love #instagood #fashion #reelitfeelit #fyp #india #motivation"

def random_sleep(min_t=2, max_t=4):
    time.sleep(random.uniform(min_t, max_t))

def get_next_link():
    if not os.path.exists(LINKS_FILE): return None
    if not os.path.exists(HISTORY_FILE): 
        with open(HISTORY_FILE, 'w') as f: pass

    with open(LINKS_FILE, 'r') as f:
        all_links = [l.strip() for l in f.readlines() if l.strip()]
    with open(HISTORY_FILE, 'r') as f:
        history = [l.strip() for l in f.readlines()]

    for link in all_links:
        if link not in history: return link
    return None

def check_and_close_ads(driver):
    if len(driver.window_handles) > 1:
        print("🚫 Ad Popup Detected! Closing immediately...")
        driver.switch_to.window(driver.window_handles[1])
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

def clean_caption(raw_text):
    if not raw_text: return "New Reel"
    # Remove old hashtags
    clean_text = re.sub(r'#\w+', '', raw_text)
    # Remove extra whitespace
    return clean_text.strip()

def download_via_sssinstagram(insta_link):
    print("🕵️ Launching Browser (Target: SSSInstagram)...")
    
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = uc.Chrome(options=options, version_main=None)
    video_path = "final_video.mp4"
    processed_caption = "New Reel" 
    
    try:
        print("🌍 Opening SSSInstagram...")
        driver.get("https://sssinstagram.com/")
        time.sleep(3)

        print("✍️ Pasting Link...")
        try:
            input_box = driver.find_element(By.ID, "main_page_text")
        except:
            input_box = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='Paste']")
            
        input_box.click()
        input_box.send_keys(insta_link)
        check_and_close_ads(driver)

        print("🖱️ Clicking Download...")
        try:
            submit_btn = driver.find_element(By.ID, "submit")
            submit_btn.click()
        except:
            input_box.send_keys(Keys.ENTER)
            
        check_and_close_ads(driver)
        print("⏳ Waiting for Result...")
        
        try:
            download_btn = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "download_link"))
            )
        except:
            download_btn = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Download')]"))
            )

        check_and_close_ads(driver)
        print("📥 Extracting Info...")
        video_url = download_btn.get_attribute("href")
        
        # Caption Logic
        try:
            p_tags = driver.find_elements(By.XPATH, "//div[contains(@class, 'result')]//p")
            raw_caption = ""
            for p in p_tags:
                text = p.text
                if len(text) > 5 and "Download" not in text:
                    raw_caption = text
                    break
            
            if raw_caption:
                processed_caption = clean_caption(raw_caption)
        except:
            pass

        if not video_url: raise Exception("Video URL Not Found")

        print(f"🔗 Video Link Found...")

        # Download
        r = requests.get(video_url, stream=True)
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                f.write(chunk)
        
        if os.path.getsize(video_path) < 50000:
             raise Exception("File too small.")

        return video_path, processed_caption

    except Exception as e:
        print(f"❌ Browser Error: {e}")
        driver.save_screenshot("error_debug.png")
        return None, None
    finally:
        driver.quit()

def upload_to_catbox(file_path):
    print("☁️ Uploading to Catbox...")
    try:
        with open(file_path, "rb") as f:
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.post("https://catbox.moe/user/api.php", 
                            data={"reqtype": "fileupload"}, 
                            files={"fileToUpload": f},
                            headers=headers)
            if r.status_code == 200: 
                return r.text.strip()
            else:
                print(f"⚠️ Catbox Error: {r.status_code}")
                return None
    except Exception as e:
        print(f"Upload Error: {e}")
    return None

def send_notification(video_url, clean_text, original_link):
    print("🚀 Preparing Post...")
    
    # --- 1. CAPTION FORMATTING ---
    # User Requirement: Text -> . . . -> Hashtags
    final_caption = f"{clean_text}\n.\n.\n.\n.\n.\n{SEO_HASHTAGS}"
    
    # --- 2. TELEGRAM (Send VIDEO, Not Link) ---
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        print(f"📨 Sending Video to Telegram...")
        try:
            # sendVideo endpoint use kar rahe hain
            # 'video' parameter mein URL dene se Telegram khud download karke play karta hai
            api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "video": video_url,  # Catbox URL (Telegram treats this as video file)
                "caption": final_caption
            }
            r = requests.post(api_url, json=payload)
            
            if r.status_code == 200:
                print("✅ Telegram Video Sent Successfully!")
            else:
                print(f"❌ Telegram Error {r.status_code}: {r.text}")
        except Exception as e:
            print(f"❌ Telegram Failed: {e}")
    else:
        print("⚠️ Telegram Config Missing.")

    # --- 3. WEBHOOK (Mandatory) ---
    if WEBHOOK_URL:
        print("📨 Sending to Webhook...")
        try:
            r = requests.post(WEBHOOK_URL, json={
                "video_url": video_url, 
                "caption": final_caption,
                "raw_caption": clean_text,
                "source": original_link
            })
            print(f"Webhook Status: {r.status_code}")
        except Exception as e:
            print(f"❌ Webhook Failed: {e}")
    else:
        print("❌ CRITICAL: WEBHOOK_URL is missing in Secrets!")

def update_history(link):
    with open(HISTORY_FILE, 'a') as f: f.write(link + "\n")

if __name__ == "__main__":
    # Webhook Check (Optional nahi hai ab)
    if not WEBHOOK_URL:
        print("❌ ERROR: Webhook URL is REQUIRED but missing.")
    
    link = get_next_link()
    if link:
        print(f"🎯 Processing: {link}")
        
        video_file, clean_text = download_via_sssinstagram(link)
        
        if video_file and os.path.exists(video_file):
            catbox_link = upload_to_catbox(video_file)
            
            if catbox_link:
                print(f"✅ Cloud Link: {catbox_link}")
                send_notification(catbox_link, clean_text, link)
                update_history(link)
                os.remove(video_file)
            else:
                print("❌ Catbox Upload Failed.")
        else:
            print("❌ Download Failed.")
            exit(1)
    else:
        print("💤 No new links.")
