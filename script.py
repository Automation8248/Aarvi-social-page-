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

def handle_popup_ads(driver):
    """
    SPECIAL FUNCTION: Black Close Button aur Ads ko band karne ke liye
    """
    print("🛡️ Checking for Popups/Ads...")
    time.sleep(2) # Ad load hone ka wait
    
    # 1. Agar naya Tab khula hai to band karo
    if len(driver.window_handles) > 1:
        print("🚫 Ad Tab Detected! Closing...")
        driver.switch_to.window(driver.window_handles[1])
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        return

    # 2. Page ke andar wala Pop-up (Black Close Button)
    try:
        # Common selectors for 'X' or Close buttons on Ad networks
        close_selectors = [
            "div[aria-label='Close']",       # Google Ads
            "span[class*='close']",          # Generic
            "div[id*='close']",              # Generic ID
            ".bs-modal-close",               # Bootstrap Modals
            "svg[data-icon='times']",        # FontAwesome X
            "div.ad-close-button",           # Custom Ad Close
            "//button[contains(text(), 'Close')]",
            "//div[text()='×']"              # Simple X text
        ]
        
        for selector in close_selectors:
            try:
                if "//" in selector: # XPath
                    btn = driver.find_element(By.XPATH, selector)
                else: # CSS
                    btn = driver.find_element(By.CSS_SELECTOR, selector)
                
                if btn.is_displayed():
                    print(f"❎ Found Ad Close Button ({selector}). Clicking...")
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(1)
                    break # Ek mil gaya to loop roko
            except:
                continue
    except Exception as e:
        print(f"⚠️ Ad check skipped: {e}")

def download_via_sssinstagram(insta_link):
    print("🕵️ Launching Browser (Target: SSSInstagram)...")
    
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    # User Agent Rotation (Security)
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = uc.Chrome(options=options, version_main=None)
    video_path = "final_video.mp4"
    
    try:
        print("🌍 Opening SSSInstagram...")
        driver.get("https://sssinstagram.com/")
        random_sleep(3, 5)

        print("✍️ Pasting Link...")
        try:
            input_box = driver.find_element(By.ID, "main_page_text")
        except:
            input_box = driver.find_element(By.CSS_SELECTOR, "input[type='text']")
            
        input_box.click()
        input_box.send_keys(insta_link)
        random_sleep(1, 2)

        print("🖱️ Clicking Download...")
        try:
            submit_btn = driver.find_element(By.ID, "submit")
            driver.execute_script("arguments[0].click();", submit_btn)
        except:
            input_box.send_keys(Keys.ENTER)

        print("⏳ Waiting for Result & Ads...")
        time.sleep(5) 

        # --- STEP 1: HANDLE AD POPUPS ---
        handle_popup_ads(driver)

        # --- STEP 2: FIND REAL DOWNLOAD BUTTON ---
        print("📥 Searching for Content...")
        video_url = None
        
        try:
            # SSSInstagram par content load hone ka wait
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "download_link"))
            )
            
            # Button click karne par kabhi-kabhi phir ad khulta hai, isliye safe click karenge
            buttons = driver.find_elements(By.CLASS_NAME, "download_link")
            for btn in buttons:
                href = btn.get_attribute("href")
                text = btn.text.lower()
                
                # Filter: Link valid ho aur 'download' text ho
                if href and "http" in href and "download" in text:
                    print(f"✅ Found Button: {text}")
                    video_url = href
                    break
                    
        except Exception as e:
            print("⚠️ Button not found via Class, trying fallback...")

        if not video_url:
            print("❌ Video URL fetch failed.")
            raise Exception("No URL Found")

        print(f"🔗 Real Video Link: {video_url[:40]}...")

        # Download
        r = requests.get(video_url, stream=True)
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                f.write(chunk)
        
        # Security Check: File Size
        if os.path.getsize(video_path) < 50000:
             raise Exception("Downloaded file is too small (Ad page).")

        return video_path

    except Exception as e:
        print(f"❌ Browser Error: {e}")
        driver.save_screenshot("error_debug.png")
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
