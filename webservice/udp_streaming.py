import subprocess

def stream_video_loop(video_path, udp_url):
    """
    영상을 반복적으로 UDP로 스트리밍하는 함수.
    
    Args:
    - video_path (str): 스트리밍할 영상 파일 경로
    - udp_url (str): 스트리밍할 UDP URL (예: udp://128.0.0.1:1234)
    """
    

    command = [
        "ffmpeg",
        "-stream_loop", "-1",  # 영상 무한 반복
        "-re",                 # 실시간 스트리밍처럼 처리
        "-i", video_path,      # 입력 파일
        "-vcodec", "libx264",  # 비디오 코덱
        "-acodec", "aac",      # 오디오 코덱
        "-f", "mpegts",        # 출력 형식
        udp_url                # UDP 스트림 URL
    ]

    try:
        print(f"스트리밍 시작: {udp_url} (영상 파일: {video_path})")
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # 프로세스를 계속 실행
        process.wait()
    except KeyboardInterrupt:
        print("\n스트리밍 중단됨.")
        process.terminate()
    except Exception as e:
        print(f"스트리밍 오류 발생: {e}")
    finally:
        process.terminate()


if __name__ == "__main__":
    # 스트리밍할 영상 파일 경로
    video_file_path = "webservice/영상데이터/streaming_sample.mp4"  # 영상 파일 경로 지정
    udp_stream_url = "udp://127.0.0.1:1235"   # UDP URL 지정

    # 스트리밍 시작
    stream_video_loop(video_file_path, udp_stream_url)
