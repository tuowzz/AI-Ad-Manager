from flask import Flask, jsonify, request
import requests
import os
import openai
from dotenv import load_dotenv

# โหลดค่าตัวแปรจากไฟล์ .env
load_dotenv()

# ✅ ตั้งค่า API Keys
ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
AD_ACCOUNT_ID = os.getenv("FACEBOOK_AD_ACCOUNT_ID")
CAMPAIGN_ID = os.getenv("FACEBOOK_CAMPAIGN_ID")
ADSET_ID = os.getenv("FACEBOOK_ADSET_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ตรวจสอบว่า API Keys ถูกต้อง
missing_keys = [key for key, value in {
    "FACEBOOK_ACCESS_TOKEN": ACCESS_TOKEN,
    "FACEBOOK_PAGE_ID": PAGE_ID,
    "FACEBOOK_AD_ACCOUNT_ID": AD_ACCOUNT_ID,
    "FACEBOOK_CAMPAIGN_ID": CAMPAIGN_ID,
    "FACEBOOK_ADSET_ID": ADSET_ID,
    "OPENAI_API_KEY": OPENAI_API_KEY
}.items() if not value]

if missing_keys:
    raise ValueError(f"❌ ขาดตัวแปรต่อไปนี้ใน .env: {', '.join(missing_keys)}")

# ตั้งค่า OpenAI API
openai.api_key = OPENAI_API_KEY

# ✅ สร้าง Flask App
app = Flask(__name__)

# ✅ Route ตรวจสอบสถานะ API
@app.route('/')
def home():
    return jsonify({"message": "✅ AI Ad Manager API is running!"})

# ✅ ฟังก์ชันดึงโพสต์จากเพจ
def get_page_posts():
    url = f"https://graph.facebook.com/v18.0/{PAGE_ID}/posts"
    params = {"fields": "message,full_picture,created_time", "access_token": ACCESS_TOKEN}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return [
            {"message": post.get("message", ""), "image": post.get("full_picture", ""), "date": post["created_time"]}
            for post in data.get("data", []) if "message" in post
        ]
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching posts: {e}")
        return []

# ✅ ฟังก์ชันดึงวิดีโอ Reels จากเพจ
def get_page_reels():
    url = f"https://graph.facebook.com/v18.0/{PAGE_ID}/videos"
    params = {"fields": "title,description,picture,source,created_time", "access_token": ACCESS_TOKEN}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return [
            {
                "title": video.get("title", ""),
                "description": video.get("description", ""),
                "thumbnail": video["picture"],
                "video_url": video["source"],
                "date": video["created_time"]
            }
            for video in data.get("data", []) if "source" in video
        ]
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching reels: {e}")
        return []

# ✅ ฟังก์ชันใช้ AI วิเคราะห์กลุ่มเป้าหมาย
def analyze_audience(audience_data):
    prompt = f"""
    นี่คือข้อมูลกลุ่มเป้าหมายจากโฆษณาที่เคยรัน:
    {audience_data}

    วิเคราะห์และสรุปว่ากลุ่มเป้าหมายที่เหมาะสมที่สุดคือกลุ่มไหน และให้คำแนะนำว่าควรยิงโฆษณาไปที่ใคร
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ OpenAI API Error: {str(e)}"

# ✅ ฟังก์ชันสร้างข้อความโฆษณาด้วย AI
def generate_ad_from_content(content, audience):
    prompt = f"""
    นี่คือคอนเทนต์จากเพจ Facebook:
    {content}

    และนี่คือข้อมูลกลุ่มเป้าหมาย:
    {audience}

    สร้างข้อความโฆษณาที่ดึงดูดลูกค้าและเหมาะกับกลุ่มเป้าหมาย
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ OpenAI API Error: {str(e)}"

# ✅ ฟังก์ชันยิงโฆษณาเข้า Messenger
def create_facebook_messenger_ad(content, image_url=None):
    url = f"https://graph.facebook.com/v18.0/act_{AD_ACCOUNT_ID}/ads"

    ad_params = {
        "name": "AI Messenger Ad",
        "campaign_id": CAMPAIGN_ID,
        "adset_id": ADSET_ID,
        "daily_budget": 300 * 100,
        "status": "ACTIVE",
        "creative": {
            "title": "แชทกับเราตอนนี้!",
            "body": content,
            "object_story_spec": {
                "page_id": PAGE_ID,
                "link_data": {
                    "message": content,
                    "call_to_action": {
                        "type": "MESSAGE_PAGE",
                        "value": {"page": PAGE_ID}
                    }
                }
            }
        },
        "access_token": ACCESS_TOKEN
    }

    if image_url:
        ad_params["creative"]["object_story_spec"]["link_data"]["picture"] = image_url

    try:
        response = requests.post(url, json=ad_params, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# ✅ API `/auto_ad`
@app.route('/auto_ad', methods=['POST'])
def auto_ad():
    posts = get_page_posts()
    reels = get_page_reels()

    if posts:
        best_content = posts[0]["message"]
        image_url = posts[0]["image"]
    elif reels:
        best_content = reels[0]["description"]
        image_url = reels[0]["thumbnail"]
    else:
        return jsonify({"error": "❌ ไม่พบโพสต์หรือ Reels ที่สามารถใช้ได้"}), 400

    audience_data = analyze_audience("ข้อมูลกลุ่มเป้าหมายจากโฆษณาที่เคยรัน")
    ad_content = generate_ad_from_content(best_content, audience_data)
    ad_response = create_facebook_messenger_ad(ad_content, image_url)

    return jsonify({
        "selected_content": best_content,
        "audience_analysis": audience_data,
        "ad_text": ad_content,
        "ad_response": ad_response
    })

# ✅ ใช้ Gunicorn เพื่อรองรับ Google Cloud Run
if __name__ == "__main__":
    from gunicorn.app.base import BaseApplication

    class StandaloneApplication(BaseApplication):
        def __init__(self, app, options=None):
            self.application = app
            self.options = options or {}
            super().__init__()

        def load_config(self):
            for key, value in self.options.items():
                self.cfg.set(key, value)

        def load(self):
            return self.application

    options = {"bind": "0.0.0.0:8080", "workers": 2}
    StandaloneApplication(app, options).run()
