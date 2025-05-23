# routers/evidence_router.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from api.manager import sse_manager
import asyncio

router = APIRouter(prefix="/evidence", tags=["Evidence"])

@router.get("/stream", response_class=StreamingResponse)
async def evidence_stream():
    queue = asyncio.Queue()
    await sse_manager.add_subscriber(queue)
    return StreamingResponse(
        sse_manager.event_generator(queue),
        media_type="text/event-stream"
    )

@router.post("/ack")
async def evidence_ack(data: dict):
    if data.get("status") not in ["received", "failed"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    if data.get("status") == "received":
        return {"id" : data.get("id"), "status": "ok"}
    if data.get("status") == "failed":
        # 재전송 로직 있어야 함 
        return {"id" : data.get("id"), "status": "fail"}


@router.post("/nfc/{id}")
async def handle_nfc(id: str):
    if id in ["1", "2", "3", "4"] :
        return {"id": id, "status" :"ok" }
    else : 
        raise HTTPException(status_code=400, detail="Invalid ID")