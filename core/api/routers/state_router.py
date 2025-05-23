# routers/press_router.py
from fastapi import APIRouter, HTTPException
from api.manager import state_manager

router = APIRouter(prefix="/press", tags=["Turn Control"])

@router.post("/{press_id}")
async def handle_button_press(press_id: str):
    if press_id not in ["prosecutor", "attorney"]:
        raise HTTPException(status_code=400, detail="Invalid ID")
    
    state_manager.set_current_pressed(press_id)
    return {"status": "ok", "role": state_manager.get_current_pressed()}