# ใช้ Python 3.9 เป็น Base Image
FROM python:3.9

# ตั้งค่า Working Directory
WORKDIR /app

# คัดลอกไฟล์ทั้งหมดไปยัง Container
COPY . /app

# ติดตั้ง Dependencies
RUN pip install --no-cache-dir -r requirements.txt

# รันแอปด้วย Gunicorn บนพอร์ต 8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
