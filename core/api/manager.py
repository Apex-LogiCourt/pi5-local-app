from fastapi import FastAPI, WebSocket, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from threading import Lock
from typing import Dict, List, Optional, Generator, AsyncGenerator
from contextlib import contextmanager
import time
import uuid


app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SSE 이벤트 관리 클래스
class SSEManager:
    def __init__(self):
        self.subscribers: List[asyncio.Queue] = []
        self.evidence_lock = Lock()
        self.initial_evidence: List[Dict] = [  # 초기 증거 데이터 더미로 넣었음
            # {
            #     "id": 1,
            #     "name": "흉기 사진",
            #     "type": "prosecutor",
            #     "description": ["현장에서 발견된 칼"],
            #     "picture": "/data/weapon.jpg"
            # }
        ]

    async def add_subscriber(self, queue: asyncio.Queue):
        with self.evidence_lock:
            # 초기 증거 데이터 전송
            for evidence in self.initial_evidence:
                await queue.put(('evidence', evidence))
            
        self.subscribers.append(queue)

    async def broadcast(self, event_type: str, data: Dict):
        # print(f"[sse_manger] 인스턴스 id : {str(uuid.uuid4())}")
        for queue in self.subscribers:
            await queue.put((event_type, data))

    def remove_subscriber(self, queue: asyncio.Queue):
        if queue in self.subscribers:
            self.subscribers.remove(queue)

    async def event_generator(self, queue: asyncio.Queue) -> AsyncGenerator[str, None]:
        try:
            while True:
                event_type, data = await queue.get()
                yield f'event: {event_type}\ndata: {json.dumps(data)}\n\n'
        except asyncio.CancelledError:
            self.remove_subscriber(queue)

    async def add_evidence(self, evidence: Dict):
        """새로운 증거를 저장하고 모든 구독자에게 즉시 브로드캐스트"""
        # 초기 증거 목록에 저장
        with self.evidence_lock:
            self.initial_evidence.append(evidence)
        # 구독자들에게 전송
        await self.broadcast('evidence', evidence)

# WebSocket 관리 클래스
class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_lock = Lock()
        self.queues: Dict[WebSocket, asyncio.Queue] = {}
        self.received_msg: str = None
        

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        with self.connection_lock:
            self.active_connections.append(websocket)
            self.queues[websocket] = asyncio.Queue()

    async def disconnect(self, websocket: WebSocket):
        with self.connection_lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        with self.connection_lock:
            for connection in self.active_connections:
                await self.queues[connection].put(message)

    async def _sender(self, websocket: WebSocket):
        """개별 클라이언트 전용 송신 루프"""
        try:
            while True:
                message = await self.queues[websocket].get()
                await websocket.send_text(message)
                await asyncio.sleep(0.1)  # 잠시 대기
        except Exception as e:
            print(type(e), e)
            print(f"WebSocket _sender 송신 오류: {e}")
            await self.disconnect(websocket)


        # Core -> HW 명령 메서드들 -------------------------------------------------
    async def send_record_start(self):
        """녹음 시작 명령 전송"""
        await self.broadcast(json.dumps({
            "event": "record_start"
        }))

    async def send_record_stop(self):
        """녹음 종료 명령 전송"""
        await self.broadcast(json.dumps({
            "event": "record_stop"
        }))

    async def send_tts_request(self, text: str = "예시입니당", voice: str = "nraewon"):
        """TTS 음성 출력 요청"""
        await self.broadcast(json.dumps({
            "type": "tts",
            "data": text,
            "voice": voice
        }))
    
    def received_stt_result(self, text: str = None) -> str:
        """STT 결과를 수신하여 저장"""
        self.received_msg = text

# 상태 관리 클래스
class StateManager:
    def __init__(self):
        self.current_preessed: str = None
        self.btn_lock = Lock()
        self.evidence_list: List[Dict] = []
        self.evidence_lock = Lock()

    def get_current_pressed(self) -> str:
        with self.btn_lock:
            return self.current_preessed

    def set_current_pressed(self, role: str):
        with self.btn_lock:
            self.current_preessed = role

    def add_evidence(self, evidence: Dict):
        with self.evidence_lock:
            self.evidence_list.append(evidence)

    def get_all_evidence(self) -> List[Dict]:
        with self.evidence_lock:
            return self.evidence_list.copy()

# 의존성 주용을 위한 인스턴스 생성
sse_manager = SSEManager()
websocket_manager = WebSocketManager()
state_manager = StateManager()

# 서버 실행
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    