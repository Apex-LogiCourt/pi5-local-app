# main.py
import sys
import asyncio
# import threading
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from api.routers import state_router, websocket_router, evidence_router
from game_controller import GameController
# from PyQt5.QtWidgets import QApplication, QPushButton, QWidget, QVBoxLayout, QLabel
# from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot
# import uvicorn
import aioconsole
import types
import verdict
from case_generation.case_builder import build_case_behind_chain

# ---------------- 터미널 테스트용 클래스 ----------------
class TerminalTest:
    def __init__(self):
        from game_controller import GameController
        self.gc = GameController.get_instance()
        from data_models import Role
        self.current_role = Role.PROSECUTOR
        self.is_running = True

    async def initialize(self):
        print("재판 시뮬레이션 초기화 중...")
        await self.gc.initialize()
        await self.gc.start_game()
        print("\n=== 재판 시뮬레이션 시작 ===")
        print("사건 개요:")
        print(self.gc._case.outline)
        print("\n참여자 정보:")
        for profile in self.gc._profiles:
            print(f"- {profile.type}: {profile.name} ({profile.age}세, {profile.gender})")
            print(f"  배경: {profile.context}")
        print("\n증거 목록:")
        for evidence in self.gc._evidences:
            print(f"- [{evidence.type}] {evidence.name}")
            for desc in evidence.description:
                print(f"  > {desc}")
        print("\n=== 재판 진행 방법 ===")
        print("1. 검사와 변호사가 번갈아가며 발언")
        print("2. 발언할 때는 그냥 텍스트 입력")
        print("3. 특별 명령어:")
        print("   - /done : 현재 발언자의 발언 종료")
        print("   - /interrogate [이름] : 해당 인물 심문 시작")
        print("   - /exit : 재판 종료")
        print("\n현재 차례: 검사")

    async def handle_input(self, user_input: str):
        # 명령어(슬래시로 시작하거나 v/V) 먼저 처리
        if user_input.startswith("/") or user_input.strip().lower() == "v":
            await self.handle_command(user_input)
        else:
            await self.gc.user_input(user_input)

    async def handle_command(self, command: str):
        from data_models import Phase, Role
        if command == "/done":
            self.gc.done()
            # 심문이 끝나고 토론 모드로 돌아올 때 current_profile을 None으로 초기화
            if hasattr(self.gc._state, 'phase') and self.gc._state.phase == Phase.DEBATE:
                self.gc._state.current_profile = None
            if self.gc._state.phase == Phase.JUDGEMENT:
                await self.show_verdict()
                self.is_running = False
            else:
                self.current_role = Role.ATTORNEY if self.current_role == Role.PROSECUTOR else Role.PROSECUTOR
                print(f"\n현재 차례: {self.current_role.label()}")
        elif command.startswith("/interrogate"):
            parts = command.split()
            if len(parts) > 1:
                target_name = " ".join(parts[1:])
                target = next((p for p in self.gc._profiles if p.name == target_name), None)
                if target:
                    print(f"\n=== {target_name} 심문 시작 ===")
                    print(f"배경: {target.context}")
                    print("심문을 종료하려면 /done을 입력하세요.")
                else:
                    print(f"오류: {target_name}을(를) 찾을 수 없습니다.")
        elif command == "/exit":
            self.is_running = False
            print("재판을 종료합니다.")
        elif command.strip().lower() == "v":
            await self.show_verdict()
            self.is_running = False

    async def show_verdict(self):
        print("\n=== 최종 판결 ===")
        result = self.gc._get_judgement()
        sys.stdout.write(result + '\n')
        sys.stdout.flush()

        # 사건의 진실 출력
        print("\n=== 사건의 진실 ===")
        # 사건 개요, 등장인물 정보 준비
        case_summary = self.gc._case.outline
        # 등장인물 character 텍스트 생성 (간단히 이름/나이/성별/배경 등)
        character_info = ""
        for p in self.gc._profiles:
            character_info += f"[{p.type}] {p.name} ({p.age}세, {p.gender}) - {p.context}\n"
        # 사건의 진실 생성
        chain = build_case_behind_chain(case_summary, character_info, self.gc._profiles)
        # 스트리밍 또는 invoke로 결과 출력
        try:
            for chunk in chain.stream({}):
                content = chunk.content if hasattr(chunk, 'content') else chunk
                sys.stdout.write(content)
                sys.stdout.flush()
        except Exception as e:
            print(f"\n[사건의 진실 생성 오류]: {e}")
        print()  # 줄바꿈

async def main():
    # GameController._get_judgement monkey patch (임시 오버라이드)
    from game_controller import GameController
    def _get_judgement_patch(cls):
        return verdict.get_judge_result(cls._state.messages)
    GameController._get_judgement = types.MethodType(_get_judgement_patch, GameController)

    test = TerminalTest()
    await test.initialize()
    while test.is_running:
        try:
            user_input = await aioconsole.ainput(f"\n[{test.current_role.label()}] > ")
            await test.handle_input(user_input)
        except KeyboardInterrupt:
            print("\n재판을 종료합니다.")
            break
        except Exception as e:
            print(f"오류 발생: {e}")

if __name__ == "__main__":
    # 기존 PyQt/uvicorn/스레드 코드 모두 주석 처리
    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)
    # threading.Thread(target=loop.run_forever, daemon=True).start()
    # async def init():
    #     gc = GameController.get_instance()
    #     await gc.initialize()
    #     await gc.start_game()
    # loop.call_soon_threadsafe(asyncio.create_task, init())
    # qt_thread = threading.Thread(target=start_qt_app, args=(loop,), daemon=True)
    # qt_thread.start()
    # uvicorn.run("main:app", host="0.0.0.0", port=8000, loop="asyncio")
    asyncio.run(main())