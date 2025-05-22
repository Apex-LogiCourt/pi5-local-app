# routers/websocket_router.py
from fastapi import APIRouter, WebSocket
import json
from manager import websocket_manager

router = APIRouter(prefix="/ws", tags=["WebSocket"])

@router.websocket("/voice-stream")
async def voice_websocket(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "stt":
                print(f"STT 수신: {message['msg']}")
                await websocket_manager.broadcast(json.dumps({
                    "type": "stt_broadcast",
                    "msg": message['msg']
                }))
                
            elif message.get("event") == "ping":
                await websocket.send_json({"event": "pong"})
                
    except Exception as e:
        print(f"WebSocket 오류: {e}")
    finally:
        await websocket_manager.disconnect(websocket)