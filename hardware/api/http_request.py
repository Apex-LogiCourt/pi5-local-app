import httpx
import asyncio
import websockets
import json
from data_models import Evidence
from devices.eink_display import update_and_sand_image

# 나중에 도커로 돌릴 때는 host를 localhost가 아닌 도커 컨테이너 core 로 바꿔주세용 
async def listen_sse_async():
    while True:
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("GET", "http://localhost:8000/evidence/stream") as response:
                    print("[HW/sse] SSE connected. wait for data...")
                    async for line in response.aiter_lines():
                        if line.strip() == "":
                            continue
                        # print(f"[HW/sse] raw: {line}")
                        asyncio.create_task(sse_data_handler(line))
                            
        except httpx.RequestError as e:
            print(f"[HW/sse] connection fail: {e}")
            await asyncio.sleep(1)

async def sse_data_handler(raw_data: str):
    """
    SSE 응답 문자열에서 Evidence 객체를 생성하여 반환합니다.
    data: {...} 형식의 데이터 처리
    """
    if raw_data.startswith("data:"):
        data = raw_data.removeprefix("data:").strip()
    else:
        return
    
    try:
        parsed = json.loads(data)
        filtered = {
            "name": parsed["name"],
            "type": parsed["type"],
            "description": parsed["description"],
            "picture": parsed["picture"]
        }
        evidence = Evidence.from_dict(filtered)
        evidence.id = parsed["id"]
        print(f"[HW/sse] {evidence}")
        asyncio.create_task(evidence_ack(id=str(evidence.id), status="received"))
        update_and_sand_image(evidence.id, evidence)
        return evidence
    except (json.JSONDecodeError, KeyError) as e:
        print(f"[HW/sse] sse data convert error: {e}")
        asyncio.create_task(evidence_ack(id=str(evidence.id), status="failed"))
        return None

async def handle_button_press(press_id: str):
    response = httpx.post(f'http://localhost:8000/api/press/{press_id}')
    data = response.json()
    # print(data)
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
    # print(data)


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
    print(f"[HW/ws] send message to server: {message}")

async def receive_messages(websocket):
    try:
        async for message in websocket:
            data = json.loads(message)
            print(f"[HW/ws] receive server message: {data.get("type")}")
            await server_event_handler(websocket, data)
    except websockets.exceptions.ConnectionClosed:
        print("[HW/ws] lost connection.")

async def server_event_handler(websocket, data: dict): #서버에서 받은 메시지 처리
    global record_audio_task # 녹음 상태 체크용 변수

    event_type = data.get("type") or data.get("event")

    # if event_type == "tts_start":
    if event_type == "tts":
        print("[HW/ws] receive TTS message")
        try:
            tts_text = data["data"]
            voice = data.get("voice")
            print(f"[HW/ws] TTS start: '{tts_text}' (voice: {voice})")
            await tts.set_playing_state(True)
            await tts.text_to_speech(tts_text, voice)
        except Exception as e:
            import traceback
            print(f"[HW/ws] TTS starting error: {e}")
            traceback.print_exc() #전체 스택 트레이스 출력

    elif event_type == "tts_end":
        print("[HW/ws] TTS end.")
        await tts.set_playing_state(False)

    elif event_type == "record_start":
        print("[HW/ws] request module to start REC.")
        state = await tts.set_rec_state(True)
        record_audio_task = asyncio.create_task(tts.record_audio("stt_temp"))

    elif event_type == "record_stop":
        print("[HW/ws] request module to stop REC.")
        await tts.set_rec_state(False)

        # record_audio가 끝날 때까지 기다림
        if record_audio_task is not None:
            await record_audio_task

        print("[HW/ws] receive STT data.")
        stt_text = tts.speech_to_text("stt_temp")
        messages = {
            "type": "stt",
            "msg" : stt_text
        }
        await send_messages(websocket, messages)
    else:
        print("[HW/ws] receive UNKNOWN EVENT: ", data)

async def websocket_client():
    uri = "ws://localhost:8000/ws/voice-stream"
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                print("[HW/ws] server connected.")
                await receive_messages(websocket)
        except Exception as e:
            print(f"[HW/ws] connection fail: {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    pass