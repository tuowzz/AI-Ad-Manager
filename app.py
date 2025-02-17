from flask import Flask, jsonify
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
SOURCE_AUDIENCE_ID = os.getenv("FACEBOOK_SOURCE_AUDIENCE_ID")  # ✅ แหล่งข้อมูลเดิม

# ตรวจสอบว่า API Keys ถูกต้อง
if not all([ACCESS_TOKEN, AD_ACCOUNT_ID, OPENAI_API_KEY, SOURCE_AUDIENCE_ID]):
    raise ValueError("❌ ค่าตัวแปร API Keys ไม่ครบ ตรวจสอบ .env")

# ตั้งค่า OpenAI API เวอร์ชันใหม่
client = openai.Client(api_key=OPENAI_API_KEY)

# สร้าง Flask App
app = Flask(__name__)

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
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
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


# ✅ ฟังก์ชันสร้าง Lookalike Audience บน Facebook Ads
def create_facebook_lookalike_audience(audience_name, description):
    url = f"https://graph.facebook.com/v18.0/act_{AD_ACCOUNT_ID}/customaudiences"

    payload = {
        "name": audience_name,
        "subtype": "LOOKALIKE",
        "lookalike_spec": {
            "type": "custom_ratio",
            "ratio": 0.01,  # ✅ Lookalike 1% 
            "country": "TH"  # ✅ ประเทศไทย
        },
        "origin_audience_id": SOURCE_AUDIENCE_ID,  # ✅ ใช้ Audience ID เดิมเป็นแหล่งข้อมูล
        "description": description,
        "access_token": ACCESS_TOKEN
    }

    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# ✅ ฟังก์ชันสร้างกลุ่มเป้าหมายอัตโนมัติ (รันอัตโนมัติเมื่อโค้ดเริ่มทำงาน)
def auto_create_audience():
    print("🚀 กำลังตรวจสอบ Facebook Token...")
    token_valid, token_message = check_facebook_token()
    if not token_valid:
        print(f"❌ Facebook Token Invalid: {token_message}")
        return

    print("🧠 กำลังใช้ AI วิเคราะห์กลุ่มเป้าหมาย...")
    audience_data = analyze_audience()
    if "❌ OpenAI API Error" in audience_data:
        print(f"❌ AI Error: {audience_data}")
        return

    print("📢 กำลังสร้าง Lookalike Audience บน Facebook...")
    audience_response = create_facebook_lookalike_audience(
        audience_name="AI Lookalike Audience - Beauty",
        description=audience_data
    )
    print(f"✅ Audience Created: {audience_response}")

# ✅ Route ตรวจสอบสถานะ API
@app.route('/')
def home():
    return jsonify({"message": "✅ AI Custom Audience API is running!"})

# ✅ ใช้ Gunicorn เพื่อรองรับ Google Cloud Run
if __name__ == "__main__":
    print("🌐 เริ่มเซิร์ฟเวอร์ Flask...")
    auto_create_audience()  # ✅ รันฟังก์ชันสร้างกลุ่มเป้าหมายอัตโนมัติ
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
