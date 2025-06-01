import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#qasync => PyQt5 + asyncio를 자연스럽게 통합 pip install qasync

import asyncio
from PyQt5.QtWidgets import QApplication
from qasync import QEventLoop, asyncSlot

from ui.screen.prosecutor_screen import ProsecutorScreen
from core.game_controller import GameController


def dummy(): pass

class TestApp:
    def __init__(self):
        self.controller = GameController.get_instance()
        self.window = ProsecutorScreen(
            game_controller=self.controller,
            on_switch_to_lawyer=dummy,
            on_request_judgement=dummy,
            on_interrogate=dummy,
            case_summary_text="⚖ 사건 개요 테스트용",
            profiles_data_list=[{'name': '김소현', 'type': 'defendant', 'gender': 'female', 'age': 29, 'context': '피고인 설명'}],
            evidences_data_list=[{'name': '독극물 잔', 'type': 'prosecutor', 'description': ['잔에서 독극물 검출됨']}]
        )

    async def run(self):
        await self.controller.initialize()
        self.window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    test = TestApp()

    with loop:
        loop.create_task(test.run())
        loop.run_forever()
