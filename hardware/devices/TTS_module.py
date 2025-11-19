import pyaudio
import wave
import random
import json
import requests
import sounddevice as sd
import soundfile as sf
import asyncio

PI5_INPUT_DEVICE_INDEX = 0 #pi에서 사용
DEFAULT_PATH = "/home/user/Desktop/swfesta/pi5-local-app/data/audio_temp/"
is_recording = False
is_playing = False

async def set_rec_state(st: bool):
    global is_recording 
    is_recording = st
    return is_recording

async def set_playing_state(st: bool):
    global is_playing
    is_playing = st
    return is_playing

def speech_to_text(filename):
    return clova_STT(DEFAULT_PATH + filename + ".wav")

async def text_to_speech(text: str, voice: str):
    path = DEFAULT_PATH + "tts_" + str(random.randint(100, 1000))
    wavpath = clova_TTS(text, voice, path)

    import os
    for _ in range(50):  # 5 sec waiting
        if os.path.exists(wavpath) and os.path.getsize(wavpath) > 0:
            break
        await asyncio.sleep(0.1)
    else:
        print(f"[TTS] warning: {wavpath} cannot found wav file.")
        return

    try:
        await play_wav(wavpath)
    except Exception as e:
        print(f"[TTS] tts playing err: {e}")
    return

async def play_wav(file_path):
    global is_playing
    data, samplerate = sf.read(file_path, dtype='float32')

    channels = data.shape[1] if data.ndim > 1 else 1

    with sd.OutputStream(samplerate=samplerate, channels=channels) as stream:
        block_size = 1024
        for i in range(0, len(data), block_size):
            if not is_playing:
                print("[TTS] stop playing.")
                break
            block = data[i:i+block_size]
            stream.write(block)
            await asyncio.sleep(0)

def print_audio_device():
    audio = pyaudio.PyAudio()
    print("Available audio input devices:")
    for i in range(audio.get_device_count()):
        dev = audio.get_device_info_by_index(i)
        if dev['maxInputChannels'] > 0:
            print(f"Index {i}: {dev['name']}")
    audio.terminate()
    return

async def record_audio(filename):
    global is_recording
    path = DEFAULT_PATH + filename + ".wav"

    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    CHUNK = 1024

    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        input_device_index=2,
                        frames_per_buffer=CHUNK)
    frames = []
    i = 0
    while is_recording:
        if i == 0: print("[STT] REC start ...")
        data = stream.read(CHUNK)
        frames.append(data)
        i+=1
        await asyncio.sleep(0.01)
    print("[STT] Recording finished.")
    stream.stop_stream()
    stream.close()
    audio.terminate()
    
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))


def convert_wav_to_aac(input_path, output_path):
    import subprocess
    command = [
        'ffmpeg',              # ffmpeg
        '-i', input_path,      # input file
        '-c:a', 'aac',         # 
        '-b:a', '192k',        # 
        output_path            # output file
    ]
    try:
        subprocess.run(command, check=True)
        print(f"[STT] AAC convert complete: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"[STT] AAC convert error: {e}")
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
        "format": "wav" # mp3 | wav
    }
    print("[TTS] request for ncloud server ...")
    response = requests.post(url=URL, headers=request_header, data=request_body)
    path = save_path + ".wav"
    if(response.status_code == 200):
        with open(path, "wb") as f:
            f.write(response.content)
    else:
        print(f"[TTS] server response error: {response.text}")
        return -1
    print(f"[TTS] {path} complete.")
    return path


#### TEST CODE ####
if __name__ == '__main__':
    print_audio_device()

    # record_audio("recoding.wav")
    # stt_text = clova_STT("recoding.wav")
    # print(stt_text)
    # tts_path = clova_TTS(stt_text, speaker="nara_call", save_path="./tts_test")
    # print(tts_path)
