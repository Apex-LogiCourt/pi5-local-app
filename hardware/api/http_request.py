import httpx
import asyncio
import websockets
import json

# 나중에 도커로 돌릴 때는 host를 localhost가 아닌 도커 컨테이너 core 로 바꿔주세용 
async def listen_sse_async(press_id: str):
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("GET", "http://localhost:8000/api/press/{press_id}") as response:
            async for line in response.aiter_lines():
                if line.startswith("data:"): # 근데 "event" 로 올듯 일단 한번찍어보세용
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
# ======

import asyncio
import websockets
import json

async def send_messages(websocket, message: dict):
    """서버로 메시지를 송신""" 
    await websocket.send(json.dumps(message))
    
    print(f"[클라이언트] 서버로 메시지 송신: {message}")


async def receive_messages(websocket):
    """서버로부터 메시지를 수신"""
    try:
        async for message in websocket:
            print(f"[클라이언트] 서버 메시지 수신: {message}")

            # tts 요청 처리 해야 함
            data = json.loads(message)
            if data.get("type") == "tts":
                print("[클라이언트] TTS 메시지 수신", data)
            #  {
                #   "type": "tts",
                #   "data": "사건은 4월 23일에 발생했습니다.",
                #   "voice": "jinho"
            #  }
    except websockets.exceptions.ConnectionClosed:
        print("[클라이언트] 서버 연결 종료")

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


async def main():
    uri = "ws://localhost:8000/ws/voice-stream"
    async with websockets.connect(uri) as websocket:
        print("[클라이언트] 서버에 연결됨")

        # 송신/수신 동시에 처리
        sender_task = asyncio.create_task(send_messages(websocket))
        receiver_task = asyncio.create_task(receive_messages(websocket))

        await asyncio.gather(sender_task, receiver_task)

if __name__ == "__main__":
    pass