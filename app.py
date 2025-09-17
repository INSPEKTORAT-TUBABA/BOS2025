import os
import cv2
import pytesseract
import numpy as np
import re
from PIL import Image
from flask import Flask, render_template, request, jsonify

# Atur jalur ke Tesseract OCR (ubah sesuai lokasi instalasi Anda)
# Untuk Windows:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def process_image(image_path):
    # 1. Menggunakan OpenCV untuk Memperbaiki Gambar
    img = cv2.imread(image_path)
    if img is None:
        return "Error: File tidak dapat dibaca.", None

    # Mengubah ke skala abu-abu
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Meningkatkan kontras dan ketajaman (jika diperlukan)
    # Ini adalah contoh sederhana, Anda bisa mencoba filter lain
    enhanced_img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    # Menggunakan Tesseract untuk membaca teks
    text = pytesseract.image_to_string(Image.fromarray(enhanced_img))

    return text

def analyze_document_text(text):
    # 2. Menganalisis Teks untuk Mendapatkan Data Relevan
    analysis_result = {
        'items': [],
        'total_amount': 0,
        'warnings': []
    }

    # Contoh regex untuk mencari pola "jumlah" dalam teks
    # Pola ini mencari nama item yang diikuti oleh angka
    # Misalnya: "Kegiatan Ekstrakurikuler: 1.500.000"
    item_pattern = re.compile(r'([\w\s]+)\s*:\s*([\d\.]+)')
    
    lines = text.split('\n')
    for line in lines:
        match = item_pattern.search(line)
        if match:
            item_name = match.group(1).strip()
            amount_str = match.group(2).replace('.', '')
            try:
                amount = int(amount_str)
                analysis_result['items'].append({'name': item_name, 'amount': amount})
                analysis_result['total_amount'] += amount
            except ValueError:
                # Menambahkan peringatan jika ada angka yang tidak valid
                analysis_result['warnings'].append(f"Peringatan: Angka tidak valid pada baris: '{line}'")

    # Contoh validasi (sesuai juknis BOS 2025)
    # Anda bisa menambahkan logika validasi yang lebih kompleks di sini
    if analysis_result['total_amount'] == 0:
        analysis_result['warnings'].append("Peringatan: Jumlah total tidak terdeteksi.")

    return analysis_result

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    # Menerima file yang diunggah
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Simpan file yang diunggah sementara
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    # Panggil fungsi pemrosesan
    extracted_text = process_image(filepath)
    analysis = analyze_document_text(extracted_text)

    # Hapus file yang sudah diproses
    os.remove(filepath)

    # Mengembalikan hasil analisis ke halaman web
    return jsonify(analysis)

if __name__ == '__main__':
    app.run(debug=True)