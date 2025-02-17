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

# ตรวจสอบ API Key
if not all([ACCESS_TOKEN, AD_ACCOUNT_ID, OPENAI_API_KEY]):
    raise ValueError("❌ API Keys ไม่ครบ ตรวจสอบ .env")

# ตั้งค่า OpenAI
openai.api_key = OPENAI_API_KEY

# สร้าง Flask App
app = Flask(__name__)

# ✅ Route ตรวจสอบสถานะ API
@app.route('/')
def home():
    return jsonify({"message": "✅ AI Custom Audience API is running!"})


# ✅ ฟังก์ชันใช้ AI วิเคราะห์กลุ่มเป้าหมาย
def analyze_audience_by_product(product_info):
    prompt = f"""
    สินค้าที่ขาย: {product_info}

    วิเคราะห์และสรุปว่าใครเป็นกลุ่มเป้าหมายที่เหมาะสมที่สุด เช่น เพศ อายุ ความสนใจ และพฤติกรรมการซื้อ
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ OpenAI API Error: {str(e)}"


# ✅ ฟังก์ชันสร้าง Custom Audience บน Facebook
def create_custom_audience(name, description, targeting_data):
    url = f"https://graph.facebook.com/v18.0/act_{AD_ACCOUNT_ID}/customaudiences"
    
    payload = {
        "name": name,
        "description": description,
        "subtype": "LOOKALIKE",
        "origin_audience_id": targeting_data,  
        "access_token": ACCESS_TOKEN
    }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        return {"audience_id": response.json().get("id"), "message": "✅ Custom Audience created successfully!"}
    else:
        return {"error": response.json()}


# ✅ API `/create_audience_from_product` สำหรับสร้างกลุ่มเป้าหมายจากสินค้า
@app.route('/create_audience_from_product', methods=['POST'])
def create_audience():
    data = request.get_json()
    product_info = data.get("product_info", "ไม่มีข้อมูลสินค้า")
    audience_name = data.get("audience_name", "Custom Audience AI")
    description = data.get("description", "สร้างโดย AI")

    if not product_info:
        return jsonify({"error": "❌ ต้องระบุข้อมูลสินค้า"}), 400

    # ใช้ AI วิเคราะห์กลุ่มเป้าหมาย
    analysis_result = analyze_audience_by_product(product_info)

    # สร้าง Custom Audience บน Facebook
    audience_response = create_custom_audience(audience_name, description, analysis_result)

    return jsonify({
        "audience_analysis": analysis_result,
        "facebook_response": audience_response
    })


# ✅ ใช้ Gunicorn เพื่อรองรับ Google Cloud Run
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
