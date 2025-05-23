# ui/chat_panel.py 예시
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QTextEdit
from PyQt5.QtGui import QPixmap, QFont, QIcon
from PyQt5.QtCore import Qt
import os

class ChatPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # 전체 경로 설정
        img_path = os.path.join("ui", "image")

        # 배경 이미지
        background_label = QLabel(self)
        background_pixmap = QPixmap(os.path.join(img_path, "background1.png"))
        background_label.setPixmap(background_pixmap)
        background_label.setScaledContents(True)
        background_label.setGeometry(0, 0, background_pixmap.width(), background_pixmap.height())

        # 증인 대사
        witness_text = QLabel("미키와인형 : 저는 아무것도 모릅니다", self)
        witness_text.setStyleSheet("color: white; font-weight: bold;")
        witness_text.setFont(QFont("Arial", 14))
        witness_text.setAlignment(Qt.AlignCenter)
        witness_text.setGeometry(150, 180, 500, 30)

        # 검사측 질문
        prosecutor_question = QLabel("검사측 질문 : 무엇을 보았죠?", self)
        prosecutor_question.setStyleSheet("color: white; background-color: black;")
        prosecutor_question.setFont(QFont("Arial", 12))
        prosecutor_question.setGeometry(180, 300, 400, 30)

        # 텍스트 입력 버튼
        text_button = QPushButton("텍스트 입력", self)
        text_button.setStyleSheet("background-color: #339999; color: white; font-weight: bold;")
        text_button.setGeometry(50, 300, 100, 30)

        # 마이크 버튼
        mic_button = QPushButton(self)
        mic_icon = QIcon(os.path.join(img_path, "mike.png"))
        mic_button.setIcon(mic_icon)
        mic_button.setIconSize(mic_icon.actualSize(mic_icon.availableSizes()[0]))
        mic_button.setGeometry(600, 300, 40, 30)

        # 전체 창 크기
        self.setFixedSize(background_pixmap.width(), background_pixmap.height())
        self.setWindowTitle("심문 화면")

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    panel = ChatPanel()
    panel.show()
    sys.exit(app.exec_())

