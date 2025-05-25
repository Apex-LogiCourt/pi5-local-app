from fastapi import FastAPI
from api.routers import state_router, websocket_router, evidence_router
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from game_controller import GameController

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
app.include_router(state_router.router)
app.include_router(websocket_router.router)
app.include_router(evidence_router.router)



if __name__ == "__main__":
    gc = GameController.get_instance()  # 게임 컨트롤러 초기화
    
    asyncio.run(gc.initialize())  # 비동기 초기화

    asyncio.run(gc.start_game())  # 게임 시
    asyncio.run(gc.record_start())  # 녹음 시작
    asyncio.run(gc.record_end())  # 녹음 종료
    
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)



    # asyncio.run(gc.start_game())  # 메서드 호출로 수정
    