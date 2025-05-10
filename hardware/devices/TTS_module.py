import pyaudio
import wave
import keyboard
import json
import requests

PI5_INPUT_DEVICE_INDEX = 0 #pi에서 사용

def speech_to_text():
    return

def text_to_speech():
    return

def print_audio_device(): #최초 실행 시 장치 인덱스 확인하는 작업 필요(print 값 확인하세요)
    audio = pyaudio.PyAudio()
    print("Available audio input devices:")
    for i in range(audio.get_device_count()):
        dev = audio.get_device_info_by_index(i)
        if dev['maxInputChannels'] > 0:
            print(f"Index {i}: {dev['name']}")
    audio.terminate()
    return

def record_audio(file_path):
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    CHUNK = 1024

    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        input_device_index=2,
                        frames_per_buffer=CHUNK)
    print("Recording... Press Enter to stop.") #녹음 제어 및 UI 표시방법??
    frames = []

    while True:
        data = stream.read(CHUNK)
        frames.append(data)
        if keyboard.is_pressed('enter'):
            break
    print("Recording finished.")
    stream.stop_stream()
    stream.close()
    audio.terminate()
    
    with wave.open(file_path, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))


# 전송 용량 줄이기 위한 aac 변환 작업. 일단 보류
def convert_wav_to_aac(input_path, output_path):
    import subprocess
    # FFmpeg를 통한 WAV를 AAC로 변환
    command = [
        'ffmpeg',              #ffmpeg 설치, 혹은 경로
        '-i', input_path,      # 입력 파일
        '-c:a', 'aac',         # AAC 코덱 사용
        '-b:a', '192k',        # 비트레이트 (192kbps, 필요에 따라 조정)
        output_path            # 출력 파일
    ]
    try:
        subprocess.run(command, check=True)
        print(f"파일 변환 성공: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"변환 중 오류 발생: {e}")
    return output_path


def clova_STT(file_path):
    from dotenv import dotenv_values
    env = dotenv_values()

    INVOKE_URL = env.get("STT_INVOKE_URL")
    SECRET_KEY = env.get("STT_SECRET_KEY")

    request_header = {
            'Accept': 'application/json;UTF-8',
            'X-CLOVASPEECH-API-KEY': SECRET_KEY
    }
    request_body = {
            'language': 'ko-KR',
            'completion': 'sync',
            'diarization': {"enable": "false"},
    }
    recoding_file = {
        'media': open(file_path, 'rb'),
        'params': (None, json.dumps(request_body, ensure_ascii=False).encode('UTF-8'), 'application/json')
    }
    response = requests.post(headers=request_header, url=INVOKE_URL + '/recognizer/upload', files=recoding_file)
    return response.json().get("text")


def clova_TTS(tts_str, speaker, save_path):
    from dotenv import dotenv_values
    env = dotenv_values()

    CLOVA_VOICE_API_KEY_ID = env.get("X-NCP-APIGW-API-KEY-ID")
    CLOVA_VOICE_API_KEY = env.get("X-NCP-APIGW-API-KEY")
    URL = "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts"

    request_header = {
        'X-NCP-APIGW-API-KEY-ID': CLOVA_VOICE_API_KEY_ID,
        'X-NCP-APIGW-API-KEY': CLOVA_VOICE_API_KEY,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    request_body = {
        "speaker": speaker,
        "volume": "0",  # -5 ~ 5
        "speed": "-1",  # -5 ~ 10
        "pitch": "0",   # -5 ~ 5
        "text": tts_str,
        "format": "mp3" # mp3 | wav
    }
    response = requests.post(url=URL, headers=request_header, data=request_body)

    path = save_path + ".mp3"
    if(response.status_code == 200):
        with open(path, "wb") as f:
            f.write(response.content)
    else:
        return -1
    return path


#### TEST CODE ####
if __name__ == '__main__':
    # print_audio_device()

    record_audio("recoding.wav")
    stt_text = clova_STT("recoding.wav")
    print(stt_text)
    tts_path = clova_TTS(stt_text, speaker="nara_call", save_path="./tts_test")
    print(tts_path)