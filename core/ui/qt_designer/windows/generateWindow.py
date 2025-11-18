import sys
import os
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5 import uic
import asyncio

class GenerateWindow(QDialog):
    # 뒤로가기 시그널
    def __init__(self, uiController, case_outline , parent=None):
        super().__init__(parent)
        self.uc = uiController
        self.case_outline = case_outline
        
        # UI 파일 로드
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'generateWindow.ui')
        uic.loadUi(ui_path, self)
        
        self._setup_ui()
        self._setup_connections()
    
    def _setup_ui(self):
        """UI 초기 설정"""
        # self.overviewText.setPlainText(self.case_outline)
        from data_models import Case
        from ui.type_writer import Typewriter
        self.typewriter = Typewriter(update_fn=self.overviewText.setHtml, html_mode=True)
        self.typewriter.enqueue(self.case_outline)
    
    def _setup_connections(self):
        """버튼 연결 설정"""
        self.backButton.clicked.connect(self._on_forward_clicked)
    
    def _on_forward_clicked(self):
        """앞으로 버튼 클릭
        다음 단계로 넘어가야함 !!!
        """
        print("앞으로 버튼 클릭됨")
        self.uc.open_prosecutor_window()
        self.close()
    
    def update_overview_text(self, text):
        """사건 개요 텍스트 업데이트 (typewriter용)"""
        self.overviewText.setHtml(text)
    


# 테스트용 메인 함수
if __name__ == "__main__":
    import asyncio
    
    async def main():
        app = QApplication(sys.argv)
        from game_controller import GameController  # 게임 컨트롤러 임포트

        gc = GameController().get_instance()  # 게임 컨트롤러 인스턴스
        
        # GameController 초기화 (비동기)
        await gc.initialize()
        await gc.start_game()

        case_outline = gc._case_data.case.outline

        window = GenerateWindow(None, case_outline)
        window.show()
        sys.exit(app.exec_())
    
    # 비동기 함수 실행
    asyncio.run(main())
