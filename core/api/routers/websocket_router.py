# routers/websocket_router.py
from fastapi import APIRouter, WebSocket
import json
import asyncio
from api.manager import websocket_manager
from game_controller import GameController

router = APIRouter(prefix="/ws", tags=["WebSocket"])

@router.websocket("/voice-stream")
async def voice_websocket(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        # 수신 전용 태스크
        receiver = asyncio.create_task(
            _receive_handler(websocket)
        )
        
        # 송신 전용 태스크
        sender = asyncio.create_task(
            websocket_manager._sender(websocket)
        )
        
        await asyncio.gather(receiver, sender)
                    
    except Exception as e:
        print(f"WebSocket 오류: {e}")
        import traceback
        print(f"스택 트레이스: {traceback.format_exc()}")
    finally:
        await websocket_manager.disconnect(websocket)


async def _receive_handler(websocket: WebSocket):
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # HW → Core : STT 결과 수신
            if message.get("type") == "stt":
                text = message.get("msg")
                print(f"STT 수신: {text}")

                # ➡ GameController 에 전달
                await GameController.get_instance().user_input(text)

    except Exception as e:
        print(f"WebSocket 오류: {e}")
        await websocket_manager.disconnect(websocket)