from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

# โหลดค่าตัวแปรจากไฟล์ .env
load_dotenv()

# ดึง API Key และ Ad Account ID จาก .env
ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
AD_ACCOUNT_ID = os.getenv("FACEBOOK_AD_ACCOUNT_ID")

# ตรวจสอบว่า API Key และ Account ID ถูกตั้งค่าหรือไม่
if not ACCESS_TOKEN or not AD_ACCOUNT_ID:
    raise ValueError("Missing FACEBOOK_ACCESS_TOKEN or FACEBOOK_AD_ACCOUNT_ID in environment variables.")

app = Flask(__name__)

# ดึงข้อมูลโฆษณาจาก Facebook Ads API
@app.route('/get_ads', methods=['GET'])
def get_ads():
    url = f"https://graph.facebook.com/v18.0/{AD_ACCOUNT_ID}/insights"
    params = {
        "fields": "impressions,clicks,cost_per_click",
        "access_token": ACCESS_TOKEN
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # เช็คว่าการเรียก API สำเร็จหรือไม่
        data = response.json()
        return jsonify(data)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500  # ถ้า API ล้มเหลว ส่ง Error กลับไป

# หน้าแรกสำหรับตรวจสอบว่า API ทำงานอยู่หรือไม่
@app.route('/')
def home():
    return "✅ AI Ad Manager API is running!"

# รันเซิร์ฟเวอร์ (ใช้สำหรับ Local Development เท่านั้น)
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
