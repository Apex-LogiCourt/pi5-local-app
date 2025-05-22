# routers/evidence_router.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from manager import sse_manager
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
    return {"status": "ok"}

@router.post("")
async def handle_nfc(data: dict):
    new_evidence = {
        "id": data.get("id"),
        "name": data.get("name"),
        "type": data.get("type"),
        "description": data.get("description", []),
        "picture": data.get("picture", "")
    }
    await sse_manager.broadcast("evidence", new_evidence)
    return {"status": "ok"}