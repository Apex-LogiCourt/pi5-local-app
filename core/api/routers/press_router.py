# routers/press_router.py
from fastapi import APIRouter, HTTPException
from manager import state_manager

router = APIRouter(prefix="/press", tags=["Turn Control"])

@router.post("/{press_id}")
async def handle_button_press(press_id: str):
    if press_id not in ["prosecutor", "attorney"]:
        raise HTTPException(status_code=400, detail="Invalid ID")
    
    state_manager.set_current_turn(press_id)
    return {"status": "ok", "turn": state_manager.get_current_turn()}