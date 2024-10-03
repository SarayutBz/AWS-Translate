from flask import Flask, request, render_template, jsonify
import boto3
import docx2txt
from PyPDF2 import PdfReader
import os
from dotenv import load_dotenv
from flask_cors import CORS

# โหลดไฟล์ .env
load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True)

# ฟังก์ชันแปลงไฟล์ PDF หรือ DOCX เป็นไฟล์ TXT
def convert_to_text(file):
    filename, file_extension = os.path.splitext(file.filename)
    if file_extension == '.pdf':
        reader = PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
        return text
    elif file_extension == '.docx':
        text = docx2txt.process(file)
        return text
    else:
        return None

# ฟังก์ชันเรียก AWS Translate
def translate_text(text, source_lang, target_lang):
    # ดึงค่า AWS credentials จาก .env
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_REGION')

    # สร้าง client ของ AWS Translate
    translate = boto3.client(
        'translate',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=aws_region
    )
    result = translate.translate_text(
        Text=text,
        SourceLanguageCode=source_lang,
        TargetLanguageCode=target_lang
    )
    return result['TranslatedText']

# Route สำหรับการแสดงหน้าอัปโหลดไฟล์
@app.route('/')
def upload_file():
    return render_template('index.html')

# Route สำหรับอัปโหลดไฟล์และแปลภาษา
@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # แปลงไฟล์เป็น text
    text = convert_to_text(file)
    if text is None:
        return jsonify({'error': 'Unsupported file type'}), 400

    # รับภาษาต้นทางและปลายทางจากฟอร์ม
    source_lang = request.form['source_lang']
    target_lang = request.form['target_lang']

    try:
        # แปลข้อความ
        translated_text = translate_text(text, source_lang, target_lang)
        return jsonify({'translated_text': translated_text}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
