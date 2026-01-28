# main.py
import sys
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import state_router, websocket_router, evidence_router
from game_controller import GameController

from PyQt5.QtWidgets import QApplication
from ui.UiController import UiController
import uvicorn
import qasync
import threading
import time
import requests


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


# ---------------- FastAPI 서버를 별도 스레드에서 실행 ----------------
def run_fastapi_server():
    print("FastAPI 서버 시작 중...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info")


def wait_for_server_ready(max_wait_time=30):
    """서버가 준비될 때까지 대기"""
    print("서버 준비 상태 확인 중...")
    for i in range(max_wait_time):
        try:
            response = requests.get("http://localhost:8000/docs", timeout=1)
            if response.status_code == 200:
                print("✅ FastAPI 서버가 준비되었습니다!")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
        print(f"서버 대기 중... ({i+1}/{max_wait_time})")
    return False


# ---------------- PyQt + asyncio 통합 실행 ----------------
async def main_async():
    # FastAPI 서버를 별도 스레드에서 시작
    print("FastAPI 서버 스레드 시작...")
    fastapi_thread = threading.Thread(target=run_fastapi_server, daemon=True)
    fastapi_thread.start()
    # 서버가 준비될 때까지 대기
    server_ready = await asyncio.get_event_loop().run_in_executor(
        None, wait_for_server_ready, 30
    )

    if not server_ready:
        print("❌ FastAPI 서버 시작에 실패했습니다!")
        return

    gc = GameController.get_instance()
    uiController = UiController.get_instance()

    # PyQt 이벤트 루프 실행 (qasync로 asyncio와 통합)
    await qasync.asyncio.sleep(0)  # 이벤트 루프가 시작되도록 함


if __name__ == "__main__":
    # qasync를 사용해서 PyQt5와 asyncio 통합
    qt_app = QApplication(sys.argv)
    
    # qasync 이벤트 루프 설정
    loop = qasync.QEventLoop(qt_app)
    asyncio.set_event_loop(loop)
    
    # 전역 변수로 loop 저장 (다른 모듈에서 접근 가능하도록)
    globals()['loop'] = loop
    
    try:
        # main_async 실행
        loop.run_until_complete(main_async())
        # PyQt 애플리케이션 실행
        loop.run_forever()
    except KeyboardInterrupt:
        print("애플리케이션 종료 중...")
    except Exception as e:
        import traceback
        print(f"애플리케이션 오류: {e}")
        traceback.print_exc()
    finally:
        loop.close()