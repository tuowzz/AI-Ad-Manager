from flask import Flask, jsonify, request
import requests
import os
import openai
from dotenv import load_dotenv

# โหลดค่าตัวแปรจากไฟล์ .env
load_dotenv()

# ตั้งค่า API Keys
ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
AD_ACCOUNT_ID = os.getenv("FACEBOOK_AD_ACCOUNT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ตรวจสอบว่า API Keys ถูกต้อง
if not all([ACCESS_TOKEN, AD_ACCOUNT_ID, OPENAI_API_KEY]):
    raise ValueError("❌ ค่าตัวแปร API Keys ไม่ครบ ตรวจสอบ .env")

# ตั้งค่า OpenAI
openai.api_key = OPENAI_API_KEY

# สร้าง Flask App
app = Flask(__name__)

# ✅ Route ตรวจสอบสถานะ API
@app.route('/')
def home():
    return jsonify({"message": "✅ AI Custom Audience API is running!"})


# ✅ ฟังก์ชันใช้ AI สร้างกลุ่มเป้าหมายที่เหมาะสม
def analyze_audience():
    prompt = """
    เรากำลังจะสร้างโฆษณาขายบลัชออน ลิปสติก และคอนซีลเลอร์
    - สินค้าเกี่ยวกับความงามและเครื่องสำอาง
    - ต้องการให้ AI วิเคราะห์กลุ่มเป้าหมายที่มีแนวโน้มสนใจผลิตภัณฑ์
    - ระบุ อายุ, เพศ, ความสนใจ และพฤติกรรม ที่เหมาะสมกับผลิตภัณฑ์

    ช่วยสรุปกลุ่มเป้าหมายที่เหมาะสมที่สุดให้หน่อย
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ OpenAI API Error: {str(e)}"


# ✅ ฟังก์ชันตรวจสอบว่า Facebook Token ใช้งานได้หรือไม่
def check_facebook_token():
    url = f"https://graph.facebook.com/v18.0/me?access_token={ACCESS_TOKEN}"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if "error" in data:
            return False, data["error"]["message"]
        return True, "✅ Token ใช้งานได้"
    except Exception as e:
        return False, str(e)


# ✅ ฟังก์ชันสร้าง Custom Audience บน Facebook Ads
def create_facebook_custom_audience(audience_name, description):
    url = f"https://graph.facebook.com/v18.0/act_{AD_ACCOUNT_ID}/customaudiences"

    payload = {
        "name": audience_name,
        "subtype": "LOOKALIKE",
        "lookalike_spec": {
            "type": "custom_ratio",
            "ratio": 0.01,
            "country": "TH"
        },
        "description": description,
        "access_token": ACCESS_TOKEN
    }

    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


# ✅ API `/create_audience` สำหรับสร้างกลุ่มเป้าหมายอัตโนมัติ
@app.route('/create_audience', methods=['POST'])
def create_audience():
    # ตรวจสอบว่า Token ใช้งานได้หรือไม่
    token_valid, token_message = check_facebook_token()
    if not token_valid:
        return jsonify({"error": f"❌ Facebook Token Invalid: {token_message}"}), 400

    # ใช้ AI วิเคราะห์กลุ่มเป้าหมาย
    audience_data = analyze_audience()

    if "❌ OpenAI API Error" in audience_data:
        return jsonify({"error": audience_data}), 400

    # สร้าง Custom Audience บน Facebook
    audience_response = create_facebook_custom_audience(
        audience_name="AI Custom Audience - Beauty",
        description=audience_data
    )

    return jsonify({
        "audience_analysis": audience_data,
        "facebook_response": audience_response
    })


# ✅ ใช้ Gunicorn เพื่อรองรับ Google Cloud Run
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
