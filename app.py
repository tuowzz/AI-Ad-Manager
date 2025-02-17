from flask import Flask, jsonify, request
import requests
import os
import openai
from dotenv import load_dotenv

# โหลดค่าตัวแปรจากไฟล์ .env
load_dotenv()

# ตั้งค่า API Keys
ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
AD_ACCOUNT_ID = os.getenv("FACEBOOK_AD_ACCOUNT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ตั้งค่า OpenAI
openai.api_key = OPENAI_API_KEY

# สร้าง Flask App
app = Flask(__name__)

# ✅ Route ตรวจสอบสถานะ API
@app.route('/')
def home():
    return jsonify({"message": "✅ AI Ad Manager API is running!"})


# ✅ ฟังก์ชันดึงโพสต์จากเพจ
def get_page_posts():
    url = f"https://graph.facebook.com/v18.0/{PAGE_ID}/posts"
    params = {
        "fields": "message,full_picture,created_time",
        "access_token": ACCESS_TOKEN
    }
    response = requests.get(url, params=params)
    data = response.json()

    posts = [
        {
            "message": post.get("message", ""),
            "image": post.get("full_picture", ""),
            "date": post["created_time"]
        }
        for post in data.get("data", []) if "message" in post
    ]
    return posts


# ✅ ฟังก์ชันดึงวิดีโอ Reels จากเพจ
def get_page_reels():
    url = f"https://graph.facebook.com/v18.0/{PAGE_ID}/videos"
    params = {
        "fields": "title,description,picture,source,created_time",
        "access_token": ACCESS_TOKEN
    }
    response = requests.get(url, params=params)
    data = response.json()

    reels = [
        {
            "title": video.get("title", ""),
            "description": video.get("description", ""),
            "thumbnail": video["picture"],
            "video_url": video["source"],
            "date": video["created_time"]
        }
        for video in data.get("data", []) if "source" in video
    ]
    return reels


# ✅ ฟังก์ชันใช้ AI วิเคราะห์กลุ่มเป้าหมาย
def analyze_audience(audience_data):
    prompt = f"""
    นี่คือข้อมูลกลุ่มเป้าหมายจากโฆษณาที่เคยรัน:
    {audience_data}

    วิเคราะห์และสรุปว่ากลุ่มเป้าหมายที่เหมาะสมที่สุดคือกลุ่มไหน และให้คำแนะนำว่าควรยิงโฆษณาไปที่ใคร
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}]
    )
    
    return response["choices"][0]["message"]["content"]


# ✅ ฟังก์ชันยิงโฆษณาเข้า Messenger
def create_facebook_messenger_ad(content, image_url=None):
    url = f"https://graph.facebook.com/v18.0/act_{AD_ACCOUNT_ID}/ads"

    ad_params = {
        "name": "AI Messenger Ad",
        "campaign_id": "YOUR_CAMPAIGN_ID",
        "adset_id": "YOUR_ADSET_ID",
        "daily_budget": 300 * 100,  # งบ 300 บาท
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
                        "value": {
                            "page": PAGE_ID
                        }
                    }
                }
            }
        },
        "access_token": ACCESS_TOKEN
    }

    if image_url:
        ad_params["creative"]["object_story_spec"]["link_data"]["picture"] = image_url

    response = requests.post(url, json=ad_params)
    return response.json()


# ✅ API `/auto_ad` ต้องถูกเรียกก่อน ระบบถึงจะสร้างโฆษณา
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
        return jsonify({"error": "ไม่พบโพสต์หรือ Reels ที่สามารถใช้ได้"}), 400

    # ใช้ AI วิเคราะห์กลุ่มเป้าหมาย
    audience_data = analyze_audience("ข้อมูลกลุ่มเป้าหมายจากโฆษณาที่เคยรัน")
    
    # ใช้ AI สร้างข้อความโฆษณา
    ad_content = generate_ad_from_content(best_content, audience_data)

    # ยิงโฆษณาไปยัง Messenger
    ad_response = create_facebook_messenger_ad(ad_content, image_url)

    return jsonify({
        "selected_content": best_content,
        "audience_analysis": audience_data,
        "ad_text": ad_content,
        "ad_response": ad_response
    })


# ✅ รันเซิร์ฟเวอร์ Flask
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
