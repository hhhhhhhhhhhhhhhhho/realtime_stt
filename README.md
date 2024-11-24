# Realtime STT using Whisper on WEB

Realtime STT webservice from udp stream is stt-ing with whisper-base

![](/templates/gif_from_videp.gif)


## Usage

```
python3 app.py
```

```
config.json

{
    "local_model_dir 은 수정되어야 합니다." : "해당 필드는 사용되지 않으므로 참고하세요.",
    "local_model_dir": "../model/whisper-base",  
    "audio_file_path": "test_wav.wav",        
    "sampling_rate": 16000,                   
    "duration": 5,                            
    "language": "ko",                         
    "task": "transcribe",
    "hls" : "hls",
    "udp_url" : "udp:127.0.0.1:portnumber"
  }
  
```
```
sampleing_rate : whisepr 는 16000 sampling rate 를 지원합니다.

task : -- 

udp_url : 송출되는 udp stream 주소를 입력해주세요. 

```

### WEB Viewer ( local network http://192.168.0.x:1235)
![](/templates/scs1.png)



## 