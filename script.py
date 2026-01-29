import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
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

# --- CAPTION SETTINGS ---
CUSTOM_TAG = "#aarvi"
SEO_HASHTAGS = "#trending #viral #instagram #reels #explore #love #instagood #fashion #reelitfeelit #fyp #india #motivation"

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

# --- AD & HUMAN LOGIC ---

def check_and_close_ads(driver):
    """Ads/Popups ko close karne ka strict logic"""
    try:
        current = driver.current_window_handle
        all_wins = driver.window_handles
        if len(all_wins) > 1:
            print("🚫 Ad Detected! Closing...")
            for win in all_wins:
                if win != current:
                    driver.switch_to.window(win)
                    driver.close()
            driver.switch_to.window(current)
    except: pass

def human_sleep(min_t=1.0, max_t=3.0):
    time.sleep(random.uniform(min_t, max_t))

def human_click(driver, element):
    try:
        actions = ActionChains(driver)
        actions.move_to_element(element).perform()
        time.sleep(random.uniform(0.3, 0.8))
        actions.click(element).perform()
    except:
        element.click()

def clean_caption(raw_text):
    if not raw_text: return "New Reel"
    clean_text = re.sub(r'#\w+', '', raw_text)
    return clean_text.strip()

def download_via_sssinstagram(insta_link):
    print("🕵️ Launching Browser (SSSInstagram Only)...")
    
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # Asli Browser Identity
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    options.add_argument(f"--user-agent={ua}")
    
    driver = uc.Chrome(options=options, version_main=144)
    video_path = "final_video.mp4"
    processed_caption = "New Reel" 
    
    try:
        print("🌍 Opening SSSInstagram...")
        driver.get("https://sssinstagram.com/")
        
        check_and_close_ads(driver)
        human_sleep(2, 3)
        
        # --- PASTE LOGIC ---
        print("✍️ Pasting Link...")
        try:
            input_box = driver.find_element(By.ID, "main_page_text")
        except:
            input_box = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='Paste']")
            
        human_click(driver, input_box)
        input_box.send_keys(insta_link) # Direct Paste
        human_sleep(0.5, 1.0)
        
        check_and_close_ads(driver)

        # --- CLICK BUTTON ---
        print("🖱️ Clicking Download...")
        try:
            submit_btn = driver.find_element(By.ID, "submit")
            human_click(driver, submit_btn)
        except:
            input_box.send_keys(Keys.ENTER)
            
        human_sleep(3, 5) # Wait for processing
        check_and_close_ads(driver)
        
        print("⏳ Waiting for Blue Download Link...")
        try:
            # Blue button ko target kar rahe hain
            download_btn = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(@class, 'download_link')]"))
            )
        except:
            download_btn = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Download')]"))
            )

        driver.execute_script("arguments[0].scrollIntoView();", download_btn)
        human_sleep(1, 2)
        
        # Video URL Uthana
        video_url = download_btn.get_attribute("href")
        print(f"🔗 URL Found: {video_url[:60]}...")
        
        # Caption Extract
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
        except: pass

        if not video_url: raise Exception("Video URL Not Found")

        # --- STRICT VIDEO DOWNLOAD LOGIC ---
        print("⬇️ Validating & Downloading Video...")
        
        headers = {"User-Agent": ua, "Referer": "https://sssinstagram.com/"}
        
        # Pehle check karo ki ye Video hai ya nahi (Stream=True)
        r = requests.get(video_url, headers=headers, stream=True)
        
        content_type = r.headers.get('Content-Type', '').lower()
        print(f"🧐 File Type Detected: {content_type}")
        
        # Agar ye 'video' nahi hai (jaise text/html), to reject karo
        if 'video' not in content_type:
            raise Exception(f"Invalid File Type: {content_type}. Expected video/mp4")

        # Download karo
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                f.write(chunk)
        
        # Size check (Video kam se kam 100KB ki honi chahiye)
        file_size = os.path.getsize(video_path)
        print(f"📁 Video Size: {file_size / 1024:.2f} KB")
        
        if file_size < 100000: # 100KB limit
             raise Exception("File too small. Likely an error page, not a video.")

        return video_path, processed_caption

    except Exception as e:
        print(f"❌ Error: {e}")
        driver.save_screenshot("error_debug.png")
        return None, None
    finally:
        try: driver.quit()
        except: pass

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
    except: pass
    return None

def send_notification(video_url, clean_text, original_link):
    print("🚀 Sending to Telegram...")
    final_caption = f"{clean_text}\n.\n.\n.\n.\n.\n{CUSTOM_TAG} {SEO_HASHTAGS}"
    
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo",
                json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "video": video_url,
                    "caption": final_caption
                }
            )
            print("✅ Telegram Sent")
        except Exception as e: print(f"❌ Telegram Error: {e}")

    if WEBHOOK_URL:
        try:
            requests.post(WEBHOOK_URL, json={
                "video_url": video_url, 
                "caption": final_caption,
                "raw_caption": clean_text,
                "source": original_link
            })
            print("✅ Webhook Sent")
        except: pass

def update_history(link):
    with open(HISTORY_FILE, 'a') as f: f.write(link + "\n")

if __name__ == "__main__":
    link = get_next_link()
    if link:
        print(f"🎯 Processing: {link}")
        video_file, clean_text = download_via_sssinstagram(link)
        
        if video_file and os.path.exists(video_file):
            catbox_link = upload_to_catbox(video_file)
            if catbox_link:
                print(f"✅ Catbox: {catbox_link}")
                send_notification(catbox_link, clean_text, link)
                update_history(link)
                os.remove(video_file)
                print("✅ All Done!")
            else:
                print("❌ Catbox Upload Failed.")
        else:
            print("❌ Download Failed.")
            exit(1)
    else:
        print("💤 No new links.")
