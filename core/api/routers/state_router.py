# routers/press_router.py
from fastapi import APIRouter, HTTPException
from api.manager import state_manager

router = APIRouter(prefix="/press", tags=["Turn Control"])

@router.post("/{press_id}")
async def handle_button_press(press_id: str):
    if press_id not in ["prosecutor", "attorney"]:
        raise HTTPException(status_code=400, detail="Invalid ID")
    
    ck = state_manager.set_current_pressed(press_id)
    if not ck :
        return {"status": "error", "message": "Game not initialized"}
    return {"status": "ok", "role": press_id}