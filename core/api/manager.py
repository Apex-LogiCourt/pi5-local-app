from fastapi import FastAPI, WebSocket, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from threading import Lock
from typing import Dict, List, Optional, Generator, AsyncGenerator
from contextlib import contextmanager


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
            {
                "id": 1,
                "name": "흉기 사진",
                "type": "prosecutor",
                "description": ["현장에서 발견된 칼"],
                "picture": "/data/weapon.jpg"
            }
        ]

    async def add_subscriber(self, queue: asyncio.Queue):
        with self.evidence_lock:
            # 초기 증거 데이터 전송
            for evidence in self.initial_evidence:
                await queue.put(('evidence', evidence))
            
        self.subscribers.append(queue)

    async def broadcast(self, event_type: str, data: Dict):
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

# WebSocket 관리 클래스
class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_lock = Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        with self.connection_lock:
            self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        with self.connection_lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        with self.connection_lock:
            for connection in self.active_connections:
                await connection.send_text(message)

# 상태 관리 클래스
class StateManager:
    def __init__(self):
        self.current_turn: str = "prosecutor"
        self.turn_lock = Lock()
        self.evidence_list: List[Dict] = []
        self.evidence_lock = Lock()

    def get_current_turn(self) -> str:
        with self.turn_lock:
            return self.current_turn

    def set_current_turn(self, turn: str):
        with self.turn_lock:
            self.current_turn = turn

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
    