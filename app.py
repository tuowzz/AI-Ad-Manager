import requests
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# โหลดค่าตัวแปรจาก .env
load_dotenv()
ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
AD_ACCOUNT_ID = os.getenv("FACEBOOK_AD_ACCOUNT_ID")
PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")

app = Flask(__name__)

# ✅ Route ตรวจสอบสถานะ API
@app.route('/')
def home():
    return jsonify({"message": "✅ AI Ad Manager API is running!"})


# ✅ สร้าง Campaign
def create_campaign():
    url = f"https://graph.facebook.com/v18.0/act_{AD_ACCOUNT_ID}/campaigns"
    params = {
        "name": "AI Messenger Campaign",
        "objective": "MESSAGES",
        "status": "ACTIVE",
        "special_ad_categories": [],
        "access_token": ACCESS_TOKEN
    }
    
    print("🔹 Creating Campaign...")
    response = requests.post(url, json=params)
    print("🔹 Campaign Response:", response.json())
    
    return response.json().get("id")


# ✅ สร้าง Ad Set
def create_adset(campaign_id):
    url = f"https://graph.facebook.com/v18.0/act_{AD_ACCOUNT_ID}/adsets"
    params = {
        "name": "AI AdSet",
        "campaign_id": campaign_id,
        "daily_budget": 300 * 100,  # งบ 300 บาท
        "billing_event": "IMPRESSIONS",
        "optimization_goal": "REPLIES",
        "targeting": {
            "geo_locations": {"countries": ["TH"]},  
            "age_min": 18,
            "age_max": 45
        },
        "status": "ACTIVE",
        "access_token": ACCESS_TOKEN
    }
    
    print("🔹 Creating Ad Set...")
    response = requests.post(url, json=params)
    print("🔹 Ad Set Response:", response.json())
    
    return response.json().get("id")


# ✅ สร้าง Ad
def create_ad(adset_id):
    url = f"https://graph.facebook.com/v18.0/act_{AD_ACCOUNT_ID}/ads"
    params = {
        "name": "AI Messenger Ad",
        "adset_id": adset_id,
        "creative": {
            "title": "แชทกับเราตอนนี้!",
            "body": "สนใจสินค้าของเรา? ทักแชทได้เลย!",
            "object_story_spec": {
                "page_id": PAGE_ID,
                "link_data": {
                    "message": "🔥 โปรโมชั่นพิเศษวันนี้! ทักแชทรับสิทธิพิเศษเลย!",
                    "call_to_action": {
                        "type": "MESSAGE_PAGE",
                        "value": {"page": PAGE_ID}
                    }
                }
            }
        },
        "status": "ACTIVE",
        "access_token": ACCESS_TOKEN
    }
    
    print("🔹 Creating Ad...")
    response = requests.post(url, json=params)
    print("🔹 Ad Response:", response.json())

    return response.json()


# ✅ API `/auto_ad` จะสร้างโฆษณาเมื่อถูกเรียก
@app.route('/auto_ad', methods=['POST'])
def auto_ad():
    print("🔹 Received API Call for /auto_ad")

    campaign_id = create_campaign()
    if not campaign_id:
        return jsonify({"error": "❌ ไม่สามารถสร้าง Campaign ได้"}), 400

    adset_id = create_adset(campaign_id)
    if not adset_id:
        return jsonify({"error": "❌ ไม่สามารถสร้าง AdSet ได้"}), 400

    ad_response = create_ad(adset_id)
    
    return jsonify({
        "campaign_id": campaign_id,
        "adset_id": adset_id,
        "ad_response": ad_response
    })


# ✅ ใช้ Gunicorn เพื่อรองรับ Google Cloud Run
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
