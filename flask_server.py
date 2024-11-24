import os
import threading
from flask import Flask, send_from_directory, render_template
from flask_socketio import SocketIO, emit
import subprocess
import numpy as np
from webservice.whisper import WhisperSTT
from webservice.config import Config

# Flask 설정
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # WebSocket 문제 해결

# Whisper STT 객체 생성
config = Config()
whisper_stt = WhisperSTT(config)

# HLS 디렉토리
HLS_DIR = "hls"
os.makedirs(HLS_DIR, exist_ok=True)

# UDP 스트림 URL
stream_url = config.get("udp_url")  # 예: "udp://127.0.0.1:1234"
def generate_hls_stream():
    """
    UDP 스트림을 HLS 형식으로 변환.
    """
    ffmpeg_command = [
        "ffmpeg",
        "-reuse", "1",              # 포트 재사용 플래그
        "-i", stream_url,           # UDP 입력
        "-c:v", "copy",             # 비디오 코덱 복사
        "-f", "hls",                # HLS 형식
        "-hls_time", "2",           # 세그먼트 길이 (2초)
        "-hls_list_size", "5",      # 최대 세그먼트 수
        "-hls_flags", "delete_segments",  # 오래된 세그먼트 삭제
        os.path.join(HLS_DIR, "output.m3u8")  # HLS 출력 경로
    ]
    print("HLS 스트림 변환 시작...")
    try:
        process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        print("HLS 생성 로그:", stdout)
        print("HLS 에러 로그:", stderr)
    except Exception as e:
        print(f"HLS 변환 실패: {e}")


def stream_audio_and_transcribe():
    """
    STT 처리를 수행하고 결과를 브라우저로 전송.
    """
    process = whisper_stt.load_audio_stream(stream_url)
    if process is None:
        print("오디오 스트림 로드 실패!")
        return
    
    buffer = b""
    try:
        while True:
            audio_data = process.stdout.read(4096)
            if not audio_data:
                continue

            buffer += audio_data
            if len(buffer) >= 16000 * 2:  # 1초 분량
                audio_array = np.frombuffer(buffer[:16000 * 2], dtype=np.int16).astype(np.float32) / 32768.0
                buffer = buffer[16000 * 2:]  # 처리된 데이터 삭제

                transcription = whisper_stt.transcribe_audio(audio_array)
                print(f"STT 결과: {transcription}")
                socketio.emit("stt_result", {"text": transcription})  # 결과 전송
                
    except Exception as e:
        print(f"STT 오류: {e}")
    finally:
        process.terminate()

# HLS 파일 제공 라우트
@app.route('/hls/<path:filename>')
def hls_stream(filename):
    """
    HLS 스트림 파일 제공.
    """
    try:
        print(f"HLS 요청: {filename}")
        return send_from_directory(HLS_DIR, filename)
    except Exception as e:
        print(f"HLS 파일 제공 오류: {e}")
        return "파일 제공 실패", 404


@app.route('/')
def index():
    """
    HTML 페이지 렌더링.
    """
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Live Stream with STT</title>
        <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    </head>
    <body>
        <h1>Live Video Streaming with STT</h1>
        <video id="video" controls autoplay style="width: 100%;"></video>
        <div id="stt-result">
            <h2>STT 결과:</h2>
            <p id="stt-text"></p>
        </div>
        <script>
            // HLS 스트림 재생
            if (Hls.isSupported()) {
                var video = document.getElementById('video');
                var hls = new Hls();
                hls.loadSource('/hls/output.m3u8');
                hls.attachMedia(video);
            } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
                video.src = '/hls/output.m3u8';
            } else {
                alert("HLS not supported on this browser.");
            }

            // STT 결과 수신
            var socket = io();
            socket.on('stt_result', function(data) {
                document.getElementById('stt-text').innerText = data.text;
            });
        </script>
    </body>
    </html>
    '''

def start_threads():
    """
    HLS 변환 및 STT 처리를 병렬로 실행.
    """
    threading.Thread(target=generate_hls_stream, daemon=True).start()
    threading.Thread(target=stream_audio_and_transcribe, daemon=True).start()

if __name__ == '__main__':
    start_threads()  # HLS 및 STT 시작
    socketio.run(app, host='0.0.0.0', port=8889)
