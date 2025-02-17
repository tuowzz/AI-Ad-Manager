from flask import Flask, jsonify, request
import requests
import os
import openai
from dotenv import load_dotenv
import threading

# โหลดค่าตัวแปรจากไฟล์ .env
load_dotenv()

# ตั้งค่า API Keys
ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
AD_ACCOUNT_ID = os.getenv("FACEBOOK_AD_ACCOUNT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ตรวจสอบว่า API Keys ถูกต้อง
if not all([ACCESS_TOKEN, PAGE_ID, AD_ACCOUNT_ID, OPENAI_API_KEY]):
    raise ValueError("❌ ค่าตัวแปร API Keys ไม่ครบ ตรวจสอบ .env")

# ตั้งค่า OpenAI
openai.api_key = OPENAI_API_KEY

# สร้าง Flask App
app = Flask(__name__)

# ✅ Route ตรวจสอบสถานะ API
@app.route('/')
def home():
    return jsonify({"message": "✅ AI Ad Manager API is running!"})


# ✅ ฟังก์ชันสร้างแคมเปญใหม่
def create_campaign():
    url = f"https://graph.facebook.com/v18.0/act_{AD_ACCOUNT_ID}/campaigns"
    params = {
        "name": "AI Messenger Campaign",
        "objective": "MESSAGES",
        "status": "ACTIVE",
        "special_ad_categories": [],
        "access_token": ACCESS_TOKEN
    }
    
    try:
        response = requests.post(url, json=params, timeout=10)
        response.raise_for_status()
        campaign_id = response.json().get("id")
        return campaign_id
    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating campaign: {e}")
        return None


# ✅ ฟังก์ชันยิงโฆษณาเข้า Messenger
def create_facebook_messenger_ad(campaign_id, content, image_url=None):
    url = f"https://graph.facebook.com/v18.0/act_{AD_ACCOUNT_ID}/ads"

    ad_params = {
        "name": "AI Messenger Ad",
        "campaign_id": campaign_id,
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


# ✅ API `/auto_ad` ต้องถูกเรียกก่อน ระบบถึงจะสร้างโฆษณา
@app.route('/auto_ad', methods=['POST'])
def auto_ad():
    # 1️⃣ สร้างแคมเปญใหม่
    campaign_id = create_campaign()
    if not campaign_id:
        return jsonify({"error": "❌ ไม่สามารถสร้างแคมเปญใหม่ได้"}), 400

    # 2️⃣ ใช้ AI วิเคราะห์กลุ่มเป้าหมาย
    audience_data = "ข้อมูลกลุ่มเป้าหมายจากโฆษณาที่เคยรัน"

    # 3️⃣ ใช้ AI สร้างข้อความโฆษณา
    ad_content = "🔥 สนใจสินค้าเราหรือไม่? แชทกับเราตอนนี้! 💬"

    # 4️⃣ ยิงโฆษณาไปยัง Messenger
    ad_response = create_facebook_messenger_ad(campaign_id, ad_content)

    return jsonify({
        "campaign_id": campaign_id,
        "audience_analysis": audience_data,
        "ad_text": ad_content,
        "ad_response": ad_response
    })


# ✅ ให้ระบบสร้างโฆษณาทันทีหลังจากเซิร์ฟเวอร์เริ่มต้น
def run_auto_ad():
    print("🚀 กำลังสร้างโฆษณาอัตโนมัติ...")
    requests.post("http://localhost:8080/auto_ad")

# ✅ ใช้ Thread ให้รัน auto_ad() อัตโนมัติ
if __name__ == "__main__":
    threading.Thread(target=run_auto_ad).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
