# main.py
import sys
import asyncio
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import state_router, websocket_router, evidence_router
from game_controller import GameController

from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
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


# ---------------- PyQt 실행 스레드 ----------------
def start_qt_app(loop):
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


# ---------------- 전체 실행 ----------------
if __name__ == "__main__":
    # 1. 루프 만들고 백그라운드 실행
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    threading.Thread(target=loop.run_forever, daemon=True).start()

    # 2. GameController 초기화 완료 후 PyQt 시작
    async def init_and_start():
        gc = GameController.get_instance()
        await gc.initialize()
        await gc.start_game()
        # 초기화 완료 후 PyQt 시작
        qt_thread = threading.Thread(target=start_qt_app, args=(loop,), daemon=True)
        qt_thread.start()
    
    loop.call_soon_threadsafe(asyncio.create_task, init_and_start())

    # 3. FastAPI 실행 (블로킹)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, loop="asyncio")