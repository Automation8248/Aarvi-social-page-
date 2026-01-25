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

def download_via_sssinstagram(insta_link):
    print("🕵️ Launching Browser (Target: SSSInstagram)...")
    
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    # User Agent lagana zaroori hai
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = uc.Chrome(options=options, version_main=None)
    video_path = "final_video.mp4"
    
    try:
        print("🌍 Opening sssinstagram.com...")
        driver.get("https://sssinstagram.com/en")
        random_sleep(3, 5)

        print("✍️ Pasting Link...")
        # SSSInstagram ka Input Box ID 'main_page_text' hota hai usually
        try:
            input_box = driver.find_element(By.ID, "main_page_text")
        except:
            # Fallback agar ID change ho jaye
            input_box = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='Paste']")
            
        input_box.click()
        input_box.send_keys(insta_link)
        random_sleep(1, 2)

        print("🖱️ Clicking Download...")
        # Button ID 'submit' hota hai
        try:
            submit_btn = driver.find_element(By.ID, "submit")
            driver.execute_script("arguments[0].click();", submit_btn)
        except:
            input_box.send_keys(Keys.ENTER)

        print("⏳ Waiting 5 seconds for result...")
        time.sleep(5) # User request: 3-5 sec wait

        # Ad Popup Handling (Agar click karne par naya tab khule)
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[1])
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

        print("📥 Finding Download Button...")
        
        video_url = None
        
        # SSSInstagram par result "download_link" class wale buttons mein aata hai
        try:
            # Wait for download links to appear
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.download_link, a.btn-success"))
            )
            
            # Find all download buttons
            buttons = driver.find_elements(By.TAG_NAME, "a")
            
            for btn in buttons:
                text = btn.text.lower()
                href = btn.get_attribute("href")
                
                # Logic: Link hona chahiye, 'sssinstagram' domain nahi hona chahiye (direct CDN link), aur text mein 'download' ho
                if href and "http" in href and "sssinstagram.com" not in href:
                    if "download" in text or "mp4" in text:
                        video_url = href
                        break
        except Exception as e:
            print(f"⚠️ Button search warning: {e}")

        if not video_url: 
            print("❌ Valid Video URL nahi mila. Page dump check kar raha hun...")
            raise Exception("Video URL Not Found")

        print(f"✅ Real Video URL Found: {video_url[:40]}...")

        # Download Logic
        print("💾 Downloading file...")
        r = requests.get(video_url, stream=True)
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                f.write(chunk)
        
        # SAFETY CHECK: File size check (Agar 50KB se kam hai to wo video nahi HTML page hai)
        file_size = os.path.getsize(video_path)
        if file_size < 50000: 
            raise Exception(f"File too small ({file_size} bytes). Download failed.")
            
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
            if r.status_code == 200: 
                return r.text.strip()
            else:
                print(f"Catbox Error: {r.text}")
                return None
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
        # Function name updated to use SSSInstagram
        video_file = download_via_sssinstagram(link)
        
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
