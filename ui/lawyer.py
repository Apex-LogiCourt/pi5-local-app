from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QSizePolicy, QMessageBox
from PyQt5.QtCore import Qt
from ui.resizable_image import ResizableImage, _get_image_path
from ui.style_constants import ROLE_TITLE_STYLE, SIDE_BUTTON_STYLE, TEXT_INPUT_STYLE, MIC_BUTTON_STYLE, DEFAULT_BUTTON_STYLE, DARK_BG_COLOR, WHITE_TEXT

class LawyerScreen(QWidget):
    def __init__(self, case_summary="", profiles="", on_next=None):
        super().__init__()
        self.case_summary = case_summary
        self.profiles = profiles
        self.on_next = on_next
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"background-color: {DARK_BG_COLOR}; color: {WHITE_TEXT};")

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(40, 30, 20, 30)
        left_layout.setSpacing(15)

        title_label = QLabel("변호사 반론")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(ROLE_TITLE_STYLE)

        btn_case = QPushButton("사건개요")
        btn_case.setStyleSheet(SIDE_BUTTON_STYLE)
        btn_case.setFixedWidth(160)
        btn_case.clicked.connect(self.show_case_dialog)

        btn_char = QPushButton("등장인물")
        btn_char.setStyleSheet(SIDE_BUTTON_STYLE)
        btn_char.setFixedWidth(160)
        btn_char.clicked.connect(self.show_profiles_dialog)

        btn_myproof = QPushButton("변호사측 증거품")
        btn_myproof.setStyleSheet(SIDE_BUTTON_STYLE)
        btn_myproof.setFixedWidth(160)

        btn_otherproof = QPushButton("검사측 증거품")
        btn_otherproof.setStyleSheet(SIDE_BUTTON_STYLE)
        btn_otherproof.setFixedWidth(160)

        btn_text = QPushButton("텍스트 입력")
        btn_text.setStyleSheet("background-color: #6c8a7a; color: white; font-size: 16px; border-radius: 6px; padding: 10px;")
        btn_text.setFixedWidth(160)

        btn_mic = QPushButton("🔴")
        btn_mic.setFixedSize(80, 80)
        btn_mic.setStyleSheet("background-color: #3b94d9; color: white; font-size: 30px; border-radius: 40px;")

        btn_judgement = QPushButton("판결 요청")
        btn_judgement.setStyleSheet(DEFAULT_BUTTON_STYLE)
        btn_judgement.setFixedWidth(180)
        btn_judgement.clicked.connect(self.request_judgement)

        left_layout.addWidget(title_label)
        left_layout.addSpacing(30)
        left_layout.addWidget(btn_case, alignment=Qt.AlignLeft)
        left_layout.addWidget(btn_char, alignment=Qt.AlignLeft)
        left_layout.addWidget(btn_myproof, alignment=Qt.AlignLeft)
        left_layout.addWidget(btn_otherproof, alignment=Qt.AlignLeft)
        left_layout.addWidget(btn_text, alignment=Qt.AlignLeft)
        left_layout.addSpacing(20)
        left_layout.addWidget(btn_mic, alignment=Qt.AlignCenter)
        left_layout.addStretch(1)
        left_layout.addWidget(btn_judgement, alignment=Qt.AlignRight)

        image_label = ResizableImage(_get_image_path("profile/lawyer.png"))
        image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(image_label, 3)
        main_layout.addLayout(left_layout, 2)

        self.setLayout(main_layout)

    def request_judgement(self):
        if self.on_next:
            self.on_next()

    def show_case_dialog(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("사건 개요")
        dlg.setText(self.case_summary)
        dlg.exec_()

    def show_profiles_dialog(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("등장인물 정보")
        dlg.setText(self.profiles)
        dlg.exec_()
