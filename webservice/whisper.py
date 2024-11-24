import os

import time
import torch
import librosa
import subprocess
import numpy as np
import cv2
from transformers import WhisperProcessor, WhisperForConditionalGeneration
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
        model = model.to("cpu")  # Nvidia T4 GPU 사용 설정
        return processor, model

    def transcribe_audio(self, audio_data):
        input_features = self.processor(
            audio_data, 
            sampling_rate=self.config.get("sampling_rate"),
            return_tensors="pt",
            return_attention_mask=True
        )
        attention_mask = input_features.attention_mask

        with torch.no_grad():
            forced_decoder_ids = self.processor.get_decoder_prompt_ids(
                language=self.config.get("language"), 
                task=self.config.get("task")
            )
            predicted_ids = self.model.generate(
                input_features.input_features,
                attention_mask=attention_mask,
                forced_decoder_ids=forced_decoder_ids
            )

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
            "ffmpeg", "-fflags", "nobuffer", "-i", stream_url, "-vn",
            "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", "-f", "wav", "-"
        ]
        return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        '''
        command = [
            "ffmpeg", "-i", stream_url, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", "-f", "wav", "-"
        ]
        return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        '''
        