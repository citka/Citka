from flask import Flask, render_template, request, send_file, after_this_request, jsonify
import yt_dlp
import os
import uuid
import re

app = Flask(__name__)
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def clean_filename(title):
    # ลบอักขระพิเศษที่ระบบไฟล์ไม่รองรับ
    return re.sub(r'[\\/*?:"<>|]', "", title)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url', '').strip()
    file_type = request.form.get('type', 'mp4')

    if not url:
        return jsonify({'error': 'กรุณาวางลิงก์ YouTube ก่อนครับ'}), 400

    file_id = str(uuid.uuid4())
    output_template = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.%(ext)s")

    if file_type == 'mp3':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        ext = 'mp3'
    else:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_template,
            'noplaylist': True,
        }
        ext = 'mp4'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_title = clean_filename(info.get('title', 'citka_download'))

        final_file = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.{ext}")
        download_name = f"{video_title}.{ext}"

        @after_this_request
        def remove_file(response):
            try:
                if os.path.exists(final_file):
                    os.remove(final_file)
            except Exception as e:
                app.logger.error(f"Error removing file: {e}")
            return response

        return send_file(
            final_file,
            as_attachment=True,
            download_name=download_name
        )

    except Exception as e:
        return jsonify({'error': f'ดาวน์โหลดไม่สำเร็จ: {str(e)}'}), 500

if __name__ == '__main__':
    # ตั้งค่า host='0.0.0.0' เผื่อเปิดใช้งานจากเครื่องอื่นในวง Wi-Fi เดียวกันได้ด้วย
    app.run(host='0.0.0.0', port=5000, debug=True)
