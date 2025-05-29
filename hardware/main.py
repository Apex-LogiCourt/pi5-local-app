import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# TODO data_models.py 파일을 hw쪽에 복사해서 사용.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from api.http_request import websocket_client, listen_sse_async
from devices import button_listener, rfid_reader
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    button_listener.button_init()
    task1 = asyncio.create_task(websocket_client())
    task2 = asyncio.create_task(rfid_reader.scan_rfid_loop())
    task3 = asyncio.create_task(listen_sse_async())
    print("[lifespan] HW module initialized.")
    yield
    task1.cancel()
    task2.cancel()
    task3.cancel()
    await asyncio.gather(task1, task2, task3, return_exceptions=True)
    rfid_reader.rfid_exit()
    button_listener.button_exit()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8300, reload=True)