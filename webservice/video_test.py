from flask import Flask, send_from_directory, render_template
import os

app = Flask(__name__)

HLS_DIR = 'hls'  # 실제 .m3u8와 .ts 파일들이 저장되는 디렉토리

@app.route('/hls/<path:filename>')
def stream_file(filename):
    """
    HLS 파일을 제공하는 경로 설정
    """
    file_path = os.path.join(HLS_DIR, filename)
    if os.path.exists(file_path):
        return send_from_directory(HLS_DIR, filename)
    else:
        return f"File {filename} not found", 404

@app.route('/')
def index():
    return render_template('index.html')  # HLS 스트리밍을 위한 HTML 파일

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8889)
