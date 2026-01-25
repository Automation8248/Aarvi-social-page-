import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import os
import requests
import re  # New Library for removing hashtags

# --- CONFIGURATION ---
LINKS_FILE = "links.txt"
HISTORY_FILE = "history.txt"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# --- SEO HASHTAGS (Ye purane hashtags ki jagah lagenge) ---
SEO_HASHTAGS = "\n\n#trending #viral #instagram #reels #explore #love #instagood #fashion #reelitfeelit #fyp #india #motivation"

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
    """
    Logic: Caption me se purane #hashtags hatao aur saaf text return karo
    """
    if not raw_text: return "New Video"
    
    # 1. Remove words starting with # (Hashtags)
    clean_text = re.sub(r'#\w+', '', raw_text)
    
    # 2. Remove extra spaces and newlines
    clean_text = clean_text.strip()
    
    return clean_text

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
        
        # Wait for download button
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
        
        # --- CAPTION EXTRACTION & CLEANING ---
        try:
            # SSSInstagram par caption <p> tag mein hota hai result box mein
            p_tags = driver.find_elements(By.XPATH, "//div[contains(@class, 'result')]//p")
            
            raw_caption = ""
            for p in p_tags:
                text = p.text
                # Ignore button text like 'Download'
                if len(text) > 5 and "Download" not in text:
                    raw_caption = text
                    break
            
            if raw_caption:
                print(f"📝 Original Caption: {raw_caption[:30]}...")
                # Function call to remove old hashtags
                processed_caption = clean_caption(raw_caption)
                print(f"✨ Cleaned Caption: {processed_caption[:30]}...")
            else:
                print("⚠️ No Caption found in text.")

        except Exception as e:
            print(f"⚠️ Caption Logic Error: {e}")

        if not video_url: raise Exception("Video URL Not Found")

        print(f"🔗 Video Link: {video_url[:40]}...")

        # Download
        r = requests.get(video_url, stream=True)
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                f.write(chunk)
        
        if os.path.getsize(video_path) < 50000:
             raise Exception("File too small (Ad page detected).")

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
                print(f"⚠️ Catbox Error: {r.status_code} - {r.text}")
                return None
    except Exception as e:
        print(f"Upload Error: {e}")
    return None

def send_notification(video_url, clean_text, original_link):
    print("🚀 Preparing Notification...")
    
    # OLD HASHTAGS HATA DIYE, AB SEO WALE JOD RAHE HAIN
    final_caption = f"{clean_text}{SEO_HASHTAGS}"
    
    # Message Body (Plain Text to avoid Markdown Errors)
    msg = f"🎥 New Video\n\n📝 {final_caption}\n\n🔗 Download: {video_url}\n\n📌 Source: {original_link}"
    
    # --- TELEGRAM ---
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        print(f"📨 Sending to Telegram...")
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}
            )
            print(f"Telegram Response: {r.status_code}")
        except Exception as e:
            print(f"❌ Telegram Failed: {e}")

    # --- WEBHOOK ---
    if WEBHOOK_URL:
        print("📨 Sending to Webhook...")
        try:
            r = requests.post(WEBHOOK_URL, json={
                "video": video_url, 
                "caption": final_caption, 
                "source": original_link
            })
        except: pass

def update_history(link):
    with open(HISTORY_FILE, 'a') as f: f.write(link + "\n")

if __name__ == "__main__":
    print("--- 🔍 CHECKING CONFIG ---")
    if not TELEGRAM_BOT_TOKEN: print("❌ TELEGRAM_BOT_TOKEN Missing")
    
    link = get_next_link()
    if link:
        print(f"🎯 Processing: {link}")
        
        # 1. Download & Clean Caption
        video_file, clean_text = download_via_sssinstagram(link)
        
        if video_file and os.path.exists(video_file):
            # 2. Upload
            catbox_link = upload_to_catbox(video_file)
            
            if catbox_link:
                print(f"✅ Catbox Link: {catbox_link}")
                # 3. Send (Clean Text + SEO Hashtags)
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
