import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import os
import requests

# --- CONFIGURATION ---
LINKS_FILE = "links.txt"
HISTORY_FILE = "history.txt"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

def random_sleep(min_t=2, max_t=5):
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

def download_via_fastdl(insta_link):
    print("🕵️ Launching Stealth Browser (Target: FastDL)...")
    
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    # User Agent lagana zaroori hai taaki block na ho
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    driver = uc.Chrome(options=options, version_main=None)
    video_path = "final_video.mp4"
    
    try:
        # Website Change: SnapInsta -> FastDl (More stable on GitHub)
        print("🌍 Opening FastDL...")
        driver.get("https://fastdl.app/en")
        random_sleep(3, 5)

        print("✍️ Pasting Link...")
        # Smart Selector: Input box dhundo
        try:
            input_box = driver.find_element(By.ID, "search-form-input")
        except:
            # Fallback: Agar ID change ho gayi to tag se dhundo
            input_box = driver.find_element(By.CSS_SELECTOR, "input[type='text']")
            
        input_box.send_keys(insta_link)
        random_sleep(1, 3)

        print("🖱️ Clicking Download...")
        try:
            # Button dhundo
            btn = driver.find_element(By.CLASS_NAME, "search-form__button")
            driver.execute_script("arguments[0].click();", btn)
        except:
            input_box.send_keys(Keys.ENTER)

        # Processing Wait
        random_sleep(5, 8) 

        print("📥 Finding Final Video Link...")
        # Download link dhundo (FastDL specific)
        try:
            download_btn = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.download-item__btn"))
            )
            video_url = download_btn.get_attribute("href")
        except:
            # Fallback for other sites logic
            print("⚠️ Standard button not found, trying generic search...")
            links = driver.find_elements(By.TAG_NAME, "a")
            video_url = None
            for l in links:
                href = l.get_attribute("href")
                if href and ".mp4" in href:
                    video_url = href
                    break
        
        if not video_url: raise Exception("Video URL nahi mila")

        print(f"✅ URL Found: {video_url[:30]}...")

        # Download
        r = requests.get(video_url, stream=True)
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                f.write(chunk)
        
        return video_path

    except Exception as e:
        print(f"❌ Browser Error: {e}")
        driver.save_screenshot("error_screenshot.png")
        return None
    finally:
        driver.quit()

def upload_to_catbox(file_path):
    print("☁️ Uploading to Catbox...")
    try:
        with open(file_path, "rb") as f:
            r = requests.post("https://catbox.moe/user/api.php", 
                            data={"reqtype": "fileupload"}, 
                            files={"fileToUpload": f})
            if r.status_code == 200: return r.text.strip()
    except Exception as e:
        print(f"Upload Error: {e}")
    return None

def send_notification(video_url, original_link):
    msg = f"🎥 **New Video Processed**\n\n🔗 **Download:** {video_url}\n\n📌 **Source:** {original_link}"
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                      json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    if WEBHOOK_URL:
        requests.post(WEBHOOK_URL, json={"video": video_url, "source": original_link})

def update_history(link):
    with open(HISTORY_FILE, 'a') as f: f.write(link + "\n")

if __name__ == "__main__":
    link = get_next_link()
    if link:
        print(f"🎯 Processing: {link}")
        video_file = download_via_fastdl(link)
        
        if video_file and os.path.exists(video_file):
            catbox_link = upload_to_catbox(video_file)
            if catbox_link:
                print(f"✅ Done: {catbox_link}")
                send_notification(catbox_link, link)
                update_history(link)
                os.remove(video_file)
            else:
                print("❌ Catbox Upload Failed.")
        else:
            print("❌ Download Failed.")
            exit(1)
    else:
        print("💤 No new links.")
