# main.py
import sys
import asyncio
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import state_router, websocket_router, evidence_router
from game_controller import GameController

from PyQt5.QtWidgets import QApplication, QPushButton, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot
import uvicorn


# main.py 상단
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

def loop_runner():
    print("[LoopThread] asyncio 루프 시작")
    loop.run_forever()

threading.Thread(target=loop_runner, daemon=True).start()


# ---------------- FastAPI 앱 구성 ----------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(state_router.router)
app.include_router(websocket_router.router)
app.include_router(evidence_router.router)


# ---------------- PyQt UI 정의 ----------------
class SignalEmitter(QObject):
    signal = pyqtSignal(str)

class PyQtApp(QWidget):
    def __init__(self, loop):
        super().__init__()
        self.loop = loop
        self.gc = GameController.get_instance()

        self.setWindowTitle("녹음 제어 UI")
        self.setFixedSize(300, 200)

        self.label = QLabel("대기 중...")
        self.signal_label = QLabel("Signal: 없음")  # GameController signal 표시용
        self.button = QPushButton("🎤 녹음 시작")
        
        self.button.clicked.connect(self.handle_record)
        # self.test_button.clicked.connect(self.handle_test_input)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.signal_label)
        layout.addWidget(self.button)
        self.setLayout(layout)

        self.signal = SignalEmitter()
        self.signal.signal.connect(self.label.setText)

        # GameController signal 연결
        self.gc._signal.connect(self.receive_game_signal)

        self.is_recording = False  # 상태 저장 변수

    @pyqtSlot(str, object)
    def receive_game_signal(self, code, arg):
        """GameController에서 오는 signal을 받는 슬롯"""
        print(f"[PyQt Signal Received] code: {code}, arg: {arg}")
        if isinstance(arg, dict) and "message" in arg:
            self.signal_label.setText(f"Signal: {code} - {arg['message']}")
        else:
            self.signal_label.setText(f"Signal: {code} - {str(arg)}")

    def handle_record(self):
        print(f"[버튼] 클릭됨 - 현재 상태: {'녹음중' if self.is_recording else '대기중'}")
        if self.gc._state.record_state :
            future = asyncio.run_coroutine_threadsafe(self._record_stop(), self.loop)
        else:
            future = asyncio.run_coroutine_threadsafe(self._record_start(), self.loop)

        def done_callback(fut):
            try:
                fut.result()
            except Exception as e:
                print(f"[버튼] 예외 발생: {type(e).__name__}: {e}")

        future.add_done_callback(done_callback)

    async def _record_start(self):
        print("[record_start] 호출 시작")
        await self.gc.record_start()
        self.signal.signal.emit("녹음 중...")
        self.button.setText("⏹️ 녹음 종료")
        self.is_recording = True
        print("[record_start] 완료")

    async def _record_stop(self):
        print("[record_stop] 호출 시작")
        await self.gc.record_end()
        self.signal.signal.emit("대기 중...")
        self.button.setText("🎤 녹음 시작")
        self.is_recording = False
        print("[record_stop] 완료")


# ---------------- PyQt 실행 스레드 ----------------
def start_qt_app(loop):
    app = QApplication(sys.argv)
    window = PyQtApp(loop)
    window.show()
    sys.exit(app.exec_())


# ---------------- 전체 실행 ----------------
if __name__ == "__main__":
    # 1. 루프 만들고 백그라운드 실행
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    threading.Thread(target=loop.run_forever, daemon=True).start()

    # 2. GameController 초기화
    async def init():
        gc = GameController.get_instance()
        await gc.initialize()
        await gc.start_game()
    loop.call_soon_threadsafe(asyncio.create_task, init())

    # 3. PyQt 시작
    qt_thread = threading.Thread(target=start_qt_app, args=(loop,), daemon=True)
    qt_thread.start()

    # 4. FastAPI 실행 (블로킹)
    uvicorn.run("main:app", host="0.0.0.0", port=8888, loop="asyncio")