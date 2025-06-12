import sys
import os
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QPixmap
import asyncio

class InterrogationWindow(QDialog):
    def __init__(self, uiController, gameController, profile, parent=None):
        super().__init__(parent)
        self.uc = uiController
        self.gc = gameController
        self.profile = profile
        self.mic_on = False


        # UI 파일 로드
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'interrogationWindow.ui')
        uic.loadUi(ui_path, self)


        type_mapping = {
            "witness": "증인",
            "reference": "참고인",
            "defendant": "피고인", 
            "victim": "피해자"
        }
        self.type = type_mapping.get(profile.type, "알 수 없음")

        
        self._setup_ui()
        self._setup_connections()
        
    def _setup_ui(self):
        """UI 초기 설정"""
        # 기본 텍스트 설정
        self.textLabel.setText("심문을 시작합니다.")
        self.profileTextLabel.setText("")
    

    

        

        
        
    def _setup_connections(self):
        """버튼 연결 설정"""
        self.backButton.clicked.connect(self._go_back)
        self.textButton.clicked.connect(self._open_text_input)
        self.micButton.clicked.connect(self._toggle_mic)
        self.smallEvidenceLabel.clicked.connect(self._show_evidence)
        self.largeEvidenceLabel.clicked.connect(self._show_evidence)
        
    def show_profile(self):
        """프로필 표시"""

    def update_dialogue(self, message):
        """대화 업데이트"""
        self.textLabel.setText(f"[{self.type}]: {message}")

        
    def set_main_text(self, text):
        """메인 텍스트 설정"""
        self.textLabel.setText(text)
        
    def _go_back(self):
        """뒤로 가기"""
        self.gc.interrogation_end()
        self.uc.isInterrogation = False
        self.close()
        
    def _open_text_input(self):
        """텍스트 입력창 열기"""

        
    def _toggle_mic(self):
        """마이크 온/오프 토글"""
        self.mic_on = not self.mic_on
        if self.mic_on:
            # 마이크 켜기
            self.micButton.setStyleSheet("""
                QPushButton{
                    image: url(:/images/mic_on.png);
                    background-color: rgb(47, 90, 104);
                    color: rgb(255, 254, 254);
                    border-radius: 10px;
                    font: 24pt "나눔고딕 ExtraBold";
                }
                QPushButton:hover{
                    background-color: rgb(67, 129, 148);
                    border-radius: 10px;
                    font: 28pt "나눔고딕 ExtraBold";
                }
                QPushButton:pressed{
                    background-color: rgb(0, 123, 255);
                    border-radius: 10px;
                    font: 28pt "나눔고딕 ExtraBold";
                }
            """)
            if self.gc:
                asyncio.create_task(self.gc.record_start())
        else:
            # 마이크 끄기
            self.micButton.setStyleSheet("""
                QPushButton{
                    image: url(:/images/mic_off.png);
                    background-color: rgb(47, 90, 104);
                    color: rgb(255, 254, 254);
                    border-radius: 10px;
                    font: 24pt "나눔고딕 ExtraBold";
                }
                QPushButton:hover{
                    background-color: rgb(67, 129, 148);
                    border-radius: 10px;
                    font: 28pt "나눔고딕 ExtraBold";
                }
                QPushButton:pressed{
                    background-color: rgb(0, 123, 255);
                    border-radius: 10px;
                    font: 28pt "나눔고딕 ExtraBold";
                }
            """)
            if self.gc:
                asyncio.create_task(self.gc.record_end())
                
    def _show_evidence(self):
        """증거품 창 표시"""
        if self.uc:
            self.uc.open_evidence_window()
            
    def set_mic_button_state(self, is_on):
        """마이크 버튼 상태 설정 (외부에서 호출용)"""
        self.mic_on = is_on
        if is_on:
            self.micButton.setStyleSheet("""
                QPushButton{
                    image: url(:/images/mic_on.png);
                    background-color: rgb(47, 90, 104);
                    color: rgb(255, 254, 254);
                    border-radius: 10px;
                    font: 24pt "나눔고딕 ExtraBold";
                }
                QPushButton:hover{
                    background-color: rgb(67, 129, 148);
                    border-radius: 10px;
                    font: 28pt "나눔고딕 ExtraBold";
                }
                QPushButton:pressed{
                    background-color: rgb(0, 123, 255);
                    border-radius: 10px;
                    font: 28pt "나눔고딕 ExtraBold";
                }
            """)
        else:
            self.micButton.setStyleSheet("""
                QPushButton{
                    image: url(:/images/mic_off.png);
                    background-color: rgb(47, 90, 104);
                    color: rgb(255, 254, 254);
                    border-radius: 10px;
                    font: 24pt "나눔고딕 ExtraBold";
                }
                QPushButton:hover{
                    background-color: rgb(67, 129, 148);
                    border-radius: 10px;
                    font: 28pt "나눔고딕 ExtraBold";
                }
                QPushButton:pressed{
                    background-color: rgb(0, 123, 255);
                    border-radius: 10px;
                    font: 28pt "나눔고딕 ExtraBold";
                }
            """)

# 테스트용 메인 함수
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 테스트용 더미 데이터
    class DummyCaseData:
        def __init__(self):
            self.profiles = []
    
    window = InterrogationWindow(None, None, DummyCaseData())
    window.show()
    
    sys.exit(app.exec_())
