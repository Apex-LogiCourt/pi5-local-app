import httpx
import asyncio
import websockets
import json

# 나중에 도커로 돌릴 때는 host를 localhost가 아닌 도커 컨테이너 core 로 바꿔주세용 
async def listen_sse_async(press_id: str):
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("GET", "http://localhost:8000/sse/evidence/stream") as response:
            async for line in response.aiter_lines():
                if line.startswith("event:"): # 근데 "event" 로 올듯 일단 한번찍어보세용
                    data = line.removeprefix("data:").strip()
                    print(f"받은 데이터: {data}")


async def handle_button_press(press_id: str):
    response = httpx.post(f'http://localhost:8000/api/press/{press_id}')
    data = response.json()
    print(data)
    # 받는 응답: {"status": "ok", "role": "prosecutor"}
    return data

async def handle_nfc(id: str):
    response = httpx.post(f'http://localhost:8000/api/press/{id}')
    data = response.json()
    print(data)
    # 받는 응답: {"id": 1, "status": "ok"}

async def evidence_ack(id: str, status: str):
    response = httpx.post('http://localhost:8000/evidence/ack', json={ "id": id, "status": status})
    # status 값은 "received" 또는 "faild" 중 하나
    # faild일 경우에 evidence 객체를 돌려줌 
    # recived 일 떄 받는 응답: {"id": 1, "status": "ok"}
    data = response.json()
    print(data)


# ===================
# WebSocket 클라이언트 
# ===============

import asyncio
import websockets
import json
import devices.TTS_module as tts

record_audio_task = None

async def send_messages(websocket, message: dict):
    """서버로 메시지를 송신""" 
    await websocket.send(json.dumps(message))
    print(f"[클라이언트] 서버로 메시지 송신: {message}")


async def receive_messages(websocket):
    try:
        async for message in websocket:
            print(f"[클라이언트] 서버 메시지 수신: {message}")
            data = json.loads(message)
            await server_event_handler(websocket, data)
    except websockets.exceptions.ConnectionClosed:
        print("[클라이언트] 서버 연결 종료")

async def server_event_handler(websocket, data: dict): #서버에서 받은 메시지 처리
    global record_audio_task

    event_type = data.get("type") or data.get("event")

    if event_type == "tts_start":
        print("[클라이언트] TTS 메시지 수신", data)
        try:
            tts_text = data["data"]
            voice = data.get("voice")
            print(f"[클라이언트] TTS 시작: '{tts_text}' (voice: {voice})")
            await tts.set_playing_state(True)
            await tts.text_to_speech(tts_text, voice)
        except Exception as e:
            import traceback
            print(f"[클라이언트] TTS 시작 오류: {e}")
            traceback.print_exc() #전체 스택 트레이스 출력

    elif event_type == "tts_end":
        print("[클라이언트] TTS 종료")
        await tts.set_playing_state(False)

    elif event_type == "record_start":
        print("[클라이언트] 녹음 시작")
        await tts.set_rec_state(True)
        await asyncio.sleep(1)
        # await tts.record_audio("stt_temp")
        record_audio_task = asyncio.create_task(tts.record_audio("stt_temp"))

    elif event_type == "record_stop":
        print("[클라이언트] 녹음 종료")
        await tts.set_rec_state(False)

        # record_audio가 끝날 때까지 기다림
        if record_audio_task is not None:
            await record_audio_task

        print("[클라이언트] STT 데이터 송신")
        stt_text = tts.speech_to_text("stt_temp")
        messages = {
            "type": "stt",
            "msg" : stt_text
        }
        await send_messages(websocket, messages)
    else:
        print("[클라이언트] 알 수 없는 이벤트 수신: ", data)


# async def send_tts_start(websocket):
#     """TTS 음성 출력 시작한다는 신호를 보냄""" 
#     await websocket.send(json.dumps({
#         "event": "tts_start"
#     }))
#     print("[클라이언트] tts_start 전송")

# async def send_tts_end(websocket):
#     """TTS 음성 출력 종료한다는 신호를 보냄"""
#     await websocket.send(json.dumps({
#         "event": "tts_end"
#     }))
#     print("[클라이언트] tts_end 전송")


async def websocket_client():
    uri = "ws://localhost:8000/ws/voice-stream"
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                print("[클라이언트] 서버에 연결됨")
                await receive_messages(websocket)
        except Exception as e:
            print(f"[클라이언트] 웹소켓 연결 오류: {e}, 3초 후 재시도")
            await asyncio.sleep(3)

if __name__ == "__main__":
    pass