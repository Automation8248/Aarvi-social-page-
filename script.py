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

# --- SEO HASHTAGS (Jo caption ke aage judenge) ---
SEO_HASHTAGS = "\n\n#trending #viral #instagram #reels #explore #love #instagood #fashion #reelitfeelit #fyp"

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
    """Ads ka wait nahi karega, bas check karke uda dega"""
    if len(driver.window_handles) > 1:
        print("🚫 Ad Popup Detected! Closing immediately...")
        driver.switch_to.window(driver.window_handles[1])
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

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
    extracted_caption = "New Reel Video" # Default caption
    
    try:
        print("🌍 Opening SSSInstagram...")
        driver.get("https://sssinstagram.com/")
        # Page load hone ka bas thoda sa wait (Zaroori hai)
        time.sleep(3)

        print("✍️ Pasting Link...")
        try:
            input_box = driver.find_element(By.ID, "main_page_text")
        except:
            input_box = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='Paste']")
            
        input_box.click()
        input_box.send_keys(insta_link)
        
        # Ad check after click (Reactive)
        check_and_close_ads(driver)

        print("🖱️ Clicking Download...")
        try:
            submit_btn = driver.find_element(By.ID, "submit")
            submit_btn.click()
        except:
            input_box.send_keys(Keys.ENTER)
            
        # Ad check after submit
        check_and_close_ads(driver)

        print("⏳ Waiting for Result (No blind wait)...")
        
        # Wait until the blue download button appears
        try:
            download_btn = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "download_link"))
            )
        except:
            # Agar class se nahi mila to text se dhundo
            download_btn = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Download')]"))
            )

        # Ad check before extracting info
        check_and_close_ads(driver)

        print("📥 Extracting Info...")
        video_url = download_btn.get_attribute("href")
        
        # --- CAPTION EXTRACTION LOGIC ---
        try:
            # Screenshot ke hisab se caption button ke niche hai.
            # Hum Result Box ke andar ka Text dhundhenge
            result_div = driver.find_element(By.CLASS_NAME, "result_overlay")
            full_text = result_div.text
            
            # Text cleaning (Download word hatana hai)
            clean_text = full_text.replace("Download", "").replace("Video", "").strip()
            
            # Agar text khali nahi hai to wahi caption hai
            if len(clean_text) > 5:
                extracted_caption = clean_text
                print(f"📝 Caption Found: {extracted_caption[:30]}...")
            else:
                # Fallback: Paragraph tag dhundo
                p_tag = result_div.find_element(By.TAG_NAME, "p")
                extracted_caption = p_tag.text
                
        except Exception as e:
            print(f"⚠️ Caption extraction minor issue: {e}")
            # Agar caption nahi mila to koi baat nahi, video zaruri hai

        if not video_url: 
            raise Exception("Video URL Not Found")

        print(f"🔗 Video Link: {video_url[:40]}...")

        # Download
        r = requests.get(video_url, stream=True)
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                f.write(chunk)
        
        # File Size Check
        if os.path.getsize(video_path) < 50000:
             raise Exception("File too small (Ad page detected).")

        return video_path, extracted_caption

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
            r = requests.post("https://catbox.moe/user/api.php", 
                            data={"reqtype": "fileupload"}, 
                            files={"fileToUpload": f})
            if r.status_code == 200: 
                return r.text.strip()
    except Exception as e:
        print(f"Upload Error: {e}")
    return None

def send_notification(video_url, caption, original_link):
    # Caption + SEO Hashtags
    final_caption = caption + SEO_HASHTAGS
    
    msg = f"🎥 **New Reel**\n\n📝 {final_caption}\n\n🔗 **Download:** {video_url}\n\n📌 **Source:** {original_link}"
    
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                      json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    if WEBHOOK_URL:
        requests.post(WEBHOOK_URL, json={"video": video_url, "caption": final_caption, "source": original_link})

def update_history(link):
    with open(HISTORY_FILE, 'a') as f: f.write(link + "\n")

if __name__ == "__main__":
    link = get_next_link()
    if link:
        print(f"🎯 Processing: {link}")
        
        # Function returns 2 things now: File Path AND Caption
        video_file, caption = download_via_sssinstagram(link)
        
        if video_file and os.path.exists(video_file):
            catbox_link = upload_to_catbox(video_file)
            if catbox_link:
                print(f"✅ Done: {catbox_link}")
                # Pass extracted caption to notification
                send_notification(catbox_link, caption, link)
                update_history(link)
                os.remove(video_file)
            else:
                print("❌ Catbox Upload Failed.")
        else:
            print("❌ Download Failed.")
            exit(1)
    else:
        print("💤 No new links.")
