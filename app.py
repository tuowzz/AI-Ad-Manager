from flask import Flask, jsonify
import requests
import os
from dotenv import load_dotenv

# โหลดค่าตัวแปรจากไฟล์ .env
load_dotenv()

# ตั้งค่าตัวแปรสำหรับ Facebook API
ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
AD_ACCOUNT_ID = os.getenv("FACEBOOK_AD_ACCOUNT_ID")

# ตรวจสอบว่า API Key และ Account ID ถูกต้อง
if not ACCESS_TOKEN or not AD_ACCOUNT_ID:
    raise ValueError("❌ ERROR: FACEBOOK_ACCESS_TOKEN หรือ FACEBOOK_AD_ACCOUNT_ID ไม่ถูกต้อง กรุณาตรวจสอบไฟล์ .env")

app = Flask(__name__)

# ✅ Route หลักสำหรับเช็คว่า API ทำงานหรือไม่
@app.route('/')
def home():
    return jsonify({"message": "✅ AI Ad Manager API is running!"})

# ✅ Route สำหรับดึงข้อมูลโฆษณาจาก Facebook Ads API
@app.route('/get_ads', methods=['GET'])
def get_ads():
    url = f"https://graph.facebook.com/v18.0/act_{AD_ACCOUNT_ID}/insights"
    params = {
        "fields": "impressions,clicks,cpc,ctr,spend,reach",
        "access_token": ACCESS_TOKEN
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()

        # ✅ ตรวจสอบ Error จาก Facebook API
        if "error" in data:
            return jsonify({"error": data["error"]["message"]}), 400

        return jsonify(data)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500  # ถ้า API ล้มเหลว ส่ง Error กลับไป

# ✅ รันเซิร์ฟเวอร์ (ใช้ Gunicorn บน Cloud Run)
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
