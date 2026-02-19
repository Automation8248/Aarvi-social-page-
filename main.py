import os
import json
import random
import requests
import datetime

# --- CONFIGURATION ---
VIDEO_FOLDER = "videos"
HISTORY_FILE = "history.json"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# Yahan maine image se dekh kar aapka exact Repo Name daal diya hai
GITHUB_REPO = "Automation8248/Aarushi-" 
BRANCH_NAME = "main"

# --- DATA GRID (Pre-saved Titles & Captions) ---

# List 1: Titles (Har bar inme se koi ek randomly select hoga)
TITLES_GRID = [
"Aaj kuch unexpected ho gaya…",
"Mujhe khud yakeen nahi hua",
"Ye socha nahi tha",
"Last tak dekhna",
"Ye galti mat karna",
"Aap bhi aisa karte ho?",
"Sach kuch aur nikla",
"Reality check mil gaya",
"Internet galat tha?",
"Maine test karke dekh liya",
"Aakhir sach pata chal gaya",
"Ye kaam karta hai ya nahi",
"Main ready nahi tha",
"Ye plan fail ho gaya",
"Ye plan successful ho gaya",
"Ye risky tha",
"Sab ulta ho gaya",
"Ye expect nahi kiya tha",
"Mujhe shock lag gaya",
"Aaj kismat test ki",
"Maine try kiya aur…",
"Aapko pata hona chahiye",
"Ye dangerous bhi ho sakta hai",
"Ye safe hai ya nahi",
"Ye allowed hai?",
"Log galat kar rahe hain",
"Ye sahi tareeka hai",
"Aaj kuch naya seekha",
"Ye pehli baar hua",
"Ye baar baar ho raha hai",
"Ye ignore mat karna",
"Shayad aapko ye dekhna chahiye",
"Ye important hai",
"Ye normal nahi hai",
"Ye kaise possible hai",
"Mujhe warning mili thi",
"Ye serious ho gaya",
"Aapko decide karna hai",
"Main confuse ho gaya",
"Aap kya karte?",
"Aap akela nahi ho",
"Sab theek ho jayega",
"Ye sunna zaroori hai",
"Shayad aap thak gaye ho",
"Mujhe samajh aa gaya",
"Aaj realise hua",
"Ye life lesson hai",
"Ye reality hai",
"Dil se baat",
"Honest moment",
"No filter",
"Ye personal hai",
"Maine accept kar liya",
"Maine change kar diya",
"Ye mushkil tha",
"Ye easy nahi tha",
"Maine give up nahi kiya",
"Aaj better feel ho raha",
"Khud ke liye kiya",
"Bas karna zaroori tha",
"Ye worth it tha",
"Ye worth it nahi tha",
"Aaj samajh aaya",
"Ye zaroori decision tha",
"Maine ignore kiya",
"Maine face kiya",
"Ye sach hai",
"Ye jhoot nikla",
"Mujhe regret hai",
"Mujhe khushi hai",
"Aaj achha din tha",
"Aaj bura din tha",
"Real talk",
"Open talk",
"Honest review",
"Honest reaction",
"Honest opinion",
"Real experience",
"Aap relate karoge",
"Shayad aap samjhoge",
"Ruko!",
"Ek second",
"Wait for it…",
"Trust me",
"Believe nahi karoge",
"Ye dekhna padega",
"Sound on karo",
"Close look",
"Dhyan se dekho",
"Miss mat karna",
"Ye dekhte hi samjh jaoge",
"Guess karo",
"Pehchano kya hai",
"Kya hua?",
"Ye kab hua?",
"Ye kyu hua?",
"Ab kya hoga?",
"Next kya hai?",
"Dekhte raho",
"End me twist",
"Loop pe chalega",
"Perfect timing",
"Rare moment",
"Lucky moment",
"Clean ya fail?",
"Real ya fake?",
"Before vs after",
"Ek baar aur dekho",
"Frame by frame",
"Slow motion me dekho",
"Fast forward dekho",
"Ye catch kiya?",
"Aapne notice kiya?",
"Camera ne pakda",
"Proof mil gaya",
"Ye record ho gaya",
"Unexpected ending",
"Worth watching",
"Repeat value",
"Next level",
"Aaj ka experience",
"Aaj ka result",
"Aaj ka experiment",
"Aaj ka update",
"Aaj ka scene",
"Aaj ka moment",
"Aaj ka review",
"Aaj ka reaction",
"Aaj ka test",
"Aaj ka comparison",
"Real vs expectation",
"Expectation vs reality",
"First attempt",
"Final result",
"Complete process",
"Step by step",
"Simple explanation",
"Easy method",
"Best tareeka",
"Sahi tareeka",
"Galat tareeka",
"Quick guide",
"Short guide",
"Basic guide",
"Beginner guide",
"Honest guide",
"Full details",
"Everything you need",
"A to Z",
"Complete truth",
"Full story",
"Real story",
"True story",
"My story",
"Public reaction",
"People reaction",
"Final decision",
"Last update",
"Important update",
"Big update"
]


# List 2: Captions (Har bar inme se koi ek randomly select hoga)
CAPTIONS_GRID = [
"Bas share karna tha ❤️",
"Aap relate karoge",
"Real moment",
"No filter",
"Bas aisa hi ho gaya",
"Kya lagta hai aapko?",
"Comment zaroor karna",
"Last tak dekha?",
"Aap hote to?",
"Sach me unexpected tha",
"Mujhe maza aaya",
"Honest reaction",
"Bas try kiya",
"Ye interesting tha",
"Repeat value",
"Kya ye normal hai?",
"Main overreact kar raha hu?",
"Aapka opinion?",
"Samajh aaye to batao",
"Ye kaise hua?",
"Trust the process",
"Learning everyday",
"Small progress",
"Just vibes",
"Enjoy the moment",
"Simple happiness",
"Feel this",
"Pure feeling",
"Dil se",
"Bas feel karo",
"Wait for it",
"Focus karo",
"Dhyan se dekho",
"Sound on",
"Loop pe dekho",
"Miss mat karna",
"Notice kiya?",
"Again dekho",
"Close look",
"Kya pakda?",
"Important hai",
"Ignore mat karo",
"Ye yaad rakhna",
"Kaam aayega",
"Save karlo",
"Future me kaam aayega",
"Share with friends",
"Kisi ko bhejo",
"Send to best friend",
"Aapko zarurat padegi",
"Daily reminder",
"Aaj ka lesson",
"Real life",
"Reality check",
"Hard truth",
"Soft truth",
"Samajhne wale samajh gaye",
"Bas itna hi",
"Aaj ka thought",
"Kuch to hai",
"Samajh rahe ho?",
"Shayad aapko chahiye tha",
"Right time",
"Perfect timing",
"Lucky moment",
"Rare moment",
"Unexpected",
"Proof mil gaya",
"Experiment successful",
"Experiment fail",
"Try worth it",
"Risk worth it",
"Not worth it",
"Again try karunga",
"Practice chal rahi hai",
"Process me hu",
"Improving slowly",
"Day by day better",
"Consistency",
"Discipline",
"No excuses",
"Keep going",
"Never stop",
"Bas shuru kiya hai",
"Journey start",
"Level up",
"Next target",
"Next goal",
"Almost there",
"Ho jayega",
"Kar lenge",
"Believe karo",
"Khud pe bharosa",
"Sab possible hai",
"Bas continue",
"Stay tuned",
"Aur aayega",
"Part 2?",
"Chahiye part 2?",
"Like karo agar pasand aaya",
"Follow karo aur dekho",
"Support karo",
"Family banate hai",
"Thank you ❤️",
"Appreciate it",
"Grateful"
]


# List 3: Fixed Hashtags (Ye har video me SAME rahega)
FIXED_HASHTAGS = """
.
.
.
.
.
#viral #trending #fyp #foryou #reels #short #shorts #ytshorts #explore #explorepage #viralvideo #trend #newvideo #content #creator #dailycontent #entertainment #fun #interesting #watchtillend #mustwatch #reality #real #moment #life #daily #people #reaction #vibes #share #support"""

# Isse AFFILIATE_HASHTAGS se badal kar INSTA_HASHTAGS kar diya hai
INSTA_HASHTAGS = """
.
.
.
.
"#viral #fyp #trending #explorepage #ytshorts"
"""

# --- HELPER FUNCTIONS ---

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, 'r') as f:
        return json.load(f)

def save_history(data):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- MAIN LOGIC ---

def run_automation():
    # 1. DELETE OLD FILES (15 Days Logic)
    history = load_history()
    today = datetime.date.today()
    new_history = []
    
    print("Checking for expired videos...")
    for entry in history:
        sent_date = datetime.date.fromisoformat(entry['date_sent'])
        days_diff = (today - sent_date).days
        
        file_path = os.path.join(VIDEO_FOLDER, entry['filename'])
        
        if days_diff >= 15:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"DELETED EXPIRED: {entry['filename']}")
        else:
            new_history.append(entry)
    
    save_history(new_history)
    history = new_history 

    # 2. PICK NEW VIDEO
    if not os.path.exists(VIDEO_FOLDER):
        os.makedirs(VIDEO_FOLDER)
        
    all_videos = [f for f in os.listdir(VIDEO_FOLDER) if f.lower().endswith(('.mp4', '.mov', '.mkv'))]
    sent_filenames = [entry['filename'] for entry in history]
    
    available_videos = [v for v in all_videos if v not in sent_filenames]
    
    if not available_videos:
        print("No new videos to send.")
        return

    video_to_send = random.choice(available_videos)
    video_path = os.path.join(VIDEO_FOLDER, video_to_send)
    
    print(f"Selected Video File: {video_to_send}")

    # 3. RANDOM SELECTION (Grid System)
    selected_title = random.choice(TITLES_GRID)
    selected_caption = random.choice(CAPTIONS_GRID)
    
    # Combine content
    full_telegram_caption = f"{selected_title}\n\n{selected_caption}\n{FIXED_HASHTAGS}"
    
    print(f"Generated Title: {selected_title}")
    print(f"Generated Caption: {selected_caption}")

    # 4. SEND TO TELEGRAM
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        print("Sending to Telegram...")
        with open(video_path, 'rb') as video_file:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
            payload = {
                'chat_id': TELEGRAM_CHAT_ID, 
                'caption': full_telegram_caption
            }
            files = {'video': video_file}
            try:
                requests.post(url, data=payload, files=files)
            except Exception as e:
                print(f"Telegram Error: {e}")

    # 5. SEND TO WEBHOOK
    if WEBHOOK_URL:
        print("Sending to Webhook...")
        # URL construction with your specific repo name
        raw_video_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{BRANCH_NAME}/{VIDEO_FOLDER}/{video_to_send}"
        # Encode spaces if any
        raw_video_url = raw_video_url.replace(" ", "%20")
        
        webhook_data = {
            "video_url": raw_video_url,
            "title": selected_title,
            "caption": selected_caption,
            "hashtags": FIXED_HASHTAGS,
            "insta_hashtags": INSTA_HASHTAGS, # Make.com mein isi naam se field aayegi
            "source": "AffiliateBot"
        }
        try:
            requests.post(WEBHOOK_URL, json=webhook_data)
            print(f"Webhook Sent: {raw_video_url}")
        except Exception as e:
            print(f"Webhook Error: {e}")

    # 6. UPDATE HISTORY
    new_history.append({
        "filename": video_to_send,
        "date_sent": today.isoformat()
    })
    save_history(new_history)
    print("Automation Complete.")

if __name__ == "__main__":
    run_automation()
