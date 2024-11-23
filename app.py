import os
import json
import time
import torch
import librosa
import numpy as np
import cv2
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import subprocess
import threading

# 설정을 관리하는 클래스
class Config:
    '''
    설정 파일을 관리하는 클래스입니다.
    
    Returns:
    - config (dict): 설정 값들을 담고 있는 딕셔너리.
    '''
    def __init__(self, config_file="config.json"):
        '''
        생성자 함수로, 설정 파일을 읽고 딕셔너리로 저장합니다.
        
        Arguments:
        - config_file (str): 설정 파일 경로. 기본값은 "config.json".
        '''
        with open(config_file, "r") as file:
            self.config = json.load(file)

    def get(self, key):
        '''
        설정 파일에서 특정 키의 값을 반환합니다.
        
        Arguments:
        - key (str): 찾고자 하는 설정 키.
        
        Returns:
        - value: 설정 값 (없으면 None 반환).
        '''
        return self.config.get(key, None)


# Whisper 모델과 프로세서를 관리하는 클래스
class WhisperSTT:
    '''
    Whisper 모델과 프로세서를 로드하고, 텍스트 변환을 담당하는 클래스입니다.
    
    Arguments:
    - config (Config): 설정 값을 담고 있는 Config 객체.
    '''
    def __init__(self, config):
        '''
        WhisperSTT 객체를 생성하여, Whisper 모델과 프로세서를 로드합니다.
        
        Arguments:
        - config (Config): 설정 값을 담고 있는 Config 객체.
        '''
        self.config = config
        self.processor, self.model = self.load_model(self.config.get("local_model_dir"))

    def load_model(self, local_dir):
        '''
        Whisper 모델과 프로세서를 로컬 디렉토리에서 로드합니다.
        
        Arguments:
        - local_dir (str): Whisper 모델이 저장된 로컬 디렉토리 경로.
        
        Returns:
        - processor (WhisperProcessor): 오디오 전처리 및 디코딩을 위한 프로세서.
        - model (WhisperForConditionalGeneration): 텍스트 변환을 위한 Whisper 모델.
        '''
        processor = WhisperProcessor.from_pretrained(local_dir)
        model = WhisperForConditionalGeneration.from_pretrained(local_dir)
        model = model.to("cuda")  # Nvidia T4 GPU 사용 설정
        return processor, model

    def transcribe_audio(self, audio_data):
        '''
        주어진 오디오 데이터를 Whisper 모델을 사용해 텍스트로 변환합니다.
        
        Arguments:
        - audio_data (numpy.ndarray): 변환할 오디오 데이터.
        
        Returns:
        - str: 변환된 텍스트.
        '''
        # 오디오 데이터를 모델 입력 형태로 변환
        input_features = self.processor(audio_data, sampling_rate=self.config.get("sampling_rate"), return_tensors="pt").input_features

        # 모델을 사용하여 텍스트 변환
        with torch.no_grad():
            forced_decoder_ids = self.processor.get_decoder_prompt_ids(language=self.config.get("language"), task=self.config.get("task"))
            predicted_ids = self.model.generate(input_features, forced_decoder_ids=forced_decoder_ids)

        # 결과 디코딩
        transcription = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        return transcription

    def load_audio_stream(self, stream_url):
        '''
        스트리밍 영상에서 오디오를 실시간으로 받아오기 위한 방법입니다.
        
        Arguments:
        - stream_url (str): 영상 스트리밍의 URL (예: udp://192.168.12.156:8000).
        
        Returns:
        - subprocess.Popen: ffmpeg 프로세스를 통해 오디오 데이터를 실시간으로 받아오는 객체.
        '''
        # ffmpeg를 사용하여 영상 스트림을 오디오로 추출합니다.
        command = [
            "ffmpeg", "-i", stream_url, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", "-f", "wav", "-"
        ]
        return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


# Flask 웹 서버와 SocketIO 설정
app = Flask(__name__)
socketio = SocketIO(app)

# WhisperSTT 객체 생성
config = Config()
whisper_stt = WhisperSTT(config)

# 영상 스트리밍을 위한 UDP 스트림 URL
stream_url = "udp://192.168.12.156:8000"

def stream_audio_and_transcribe():
    '''
    스트리밍 영상을 받아서 오디오를 추출하고, STT를 실시간으로 처리하여 웹 페이지에 전송하는 함수입니다.
    
    Arguments:
    - 없음 (글로벌 변수 `stream_url` 사용).
    '''
    process = whisper_stt.load_audio_stream(stream_url)
    
    while True:
        # ffmpeg에서 출력되는 오디오 데이터를 받아와 STT 처리
        audio_data = process.stdout.read(1024)
        
        if len(audio_data) > 0:
            try:
                audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
                transcription = whisper_stt.transcribe_audio(audio_array)
                socketio.emit("transcription", {"text": transcription})  # 웹에 실시간 텍스트 전송
            except Exception as e:
                print(f"Error processing audio: {e}")
        
        time.sleep(0.1)  # 실시간 처리를 위한 잠깐의 딜레이

@app.route('/')
def index():
    '''
    웹 페이지 렌더링 함수
    
    Arguments:
    - 없음
    
    Returns:
    - HTML 페이지 (index.html).
    '''
    return render_template('index.html')

def start_streaming_thread():
    '''
    비동기적으로 영상 스트리밍과 STT 처리 시작
    
    Arguments:
    - 없음
    
    Returns:
    - 없음
    '''
    threading.Thread(target=stream_audio_and_transcribe, daemon=True).start()

if __name__ == '__main__':
    '''
    애플리케이션 실행 함수
    
    Arguments:
    - 없음
    
    Returns:
    - 없음
    '''
    start_streaming_thread()  # 비동기적으로 스트리밍 시작
    socketio.run(app, host='0.0.0.0', port=5000)
