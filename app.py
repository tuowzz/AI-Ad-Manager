from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

# โหลด API Key จาก .env
load_dotenv()
ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
AD_ACCOUNT_ID = os.getenv("AD_ACCOUNT_ID")

app = Flask(__name__)

# ดึงข้อมูลโฆษณาจาก Facebook Ads API
@app.route('/get_ads', methods=['GET'])
def get_ads():
    url = f"https://graph.facebook.com/v18.0/{AD_ACCOUNT_ID}/insights"
    params = {
        "fields": "impressions,clicks,cost_per_click",
        "access_token": ACCESS_TOKEN
    }
    response = requests.get(url, params=params)
    return jsonify(response.json())

# หน้าหลัก
@app.route('/')
def home():
    return "AI Ad Manager API is running!"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
