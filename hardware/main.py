from fastapi import FastAPI
# from api.routers import state_router, websocket_router, evidence_router
from fastapi.middleware.cors import CORSMiddleware
# from api.manager import sse_manager, websocket_manager, state_manager
import asyncio
from hardware.api.http_request import websocket_client
from hardware.devices import button_listener, rfid_reader
import time
app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
# app.include_router(state_router.router)
# app.include_router(websocket_router.router)
# app.include_router(evidence_router.router)

async def hw_main():
    button_listener.button_init()
    tasks = [
        asyncio.create_task(websocket_client()),
        asyncio.create_task(rfid_reader.scan_rfid_loop())
    ]
    print("[hw-main] HW 모듈 실행 완료")
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8300, reload=True)
    asyncio.run(hw_main())