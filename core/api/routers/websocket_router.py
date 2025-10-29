# routers/websocket_router.py
from fastapi import APIRouter, WebSocket
import json
import asyncio
from api.manager import websocket_manager
from game_controller import GameController
from data_models import Phase

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
                should_switch_turn = await GameController.get_instance().user_input(text)

                # STT 처리 후 자동 턴 전환
                gc = GameController.get_instance()
                print(f"[디버그] should_switch_turn: {should_switch_turn}, phase: {gc._state.phase}, current_turn: {gc._state.turn.label()}")

                if should_switch_turn:
                    if gc._state.phase == Phase.DEBATE:
                        GameController._switch_turn()
                        current_turn = gc._state.turn
                        print(f"[자동 턴 전환] 다음 차례: {current_turn.label()}")

                        # 턴 전환을 WebSocket으로 알림
                        turn_change_msg = json.dumps({
                            "type": "turn_change",
                            "current_turn": current_turn.value,
                            "current_turn_label": current_turn.label()
                        })
                        await websocket_manager.broadcast(turn_change_msg)
                    else:
                        print(f"[경고] Phase가 DEBATE가 아님: {gc._state.phase}")

    except Exception as e:
        print(f"WebSocket 오류: {e}")
        await websocket_manager.disconnect(websocket)