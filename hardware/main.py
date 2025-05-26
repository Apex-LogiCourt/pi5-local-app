from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from api.http_request import websocket_client
from devices import button_listener, rfid_reader
import time
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    button_listener.button_init()
    task1 = asyncio.create_task(websocket_client())
    task2 = asyncio.create_task(rfid_reader.scan_rfid_loop())
    print("[lifespan] HW module initialized.")
    yield
    task1.cancel()
    task2.cancel()
    await asyncio.gather(task1, task2, return_exceptions=True)
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