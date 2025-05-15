from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QSizePolicy, QMessageBox, QGridLayout
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from ui.resizable_image import ResizableImage, _get_image_path
from ui.style_constants import (
    ROLE_TITLE_STYLE, DEFAULT_BUTTON_STYLE, DARK_BG_COLOR, WHITE_TEXT
)
from core.controller import CaseDataManager  # ✅ 증거 데이터 가져오기 위해 import

class ProsecutorScreen(QWidget):
    def __init__(self, case_summary="", profiles="", on_next=None):
        super().__init__()
        self.case_summary = case_summary
        self.profiles = profiles
        self.on_next = on_next

        self.evidences = CaseDataManager.get_evidences() or []  # ✅ 증거 저장
        self.mic_on = False
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"background-color: {DARK_BG_COLOR}; color: {WHITE_TEXT};")

        title_label = QLabel("검사 주장")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            background-color: black;
            color: white;
            font-size: 40px;
            font-weight: bold;
            padding: 10px;
            border-radius: 6px;
        """)
        title_label.setFixedWidth(260)

        title_wrapper = QHBoxLayout()
        title_wrapper.addStretch(1)
        title_wrapper.addWidget(title_label)
        title_wrapper.addStretch(1)

        def make_invisible_button(text, handler=None):
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: white;
                    font-size: 30px;
                    font-weight: bold;
                    border: none;
                }
                QPushButton:hover {
                    font-size: 33px;
                }
            """)
            btn.setMinimumSize(300, 100)
            if handler:
                btn.clicked.connect(handler)
            return btn

        def make_input_button(text):
            btn = QPushButton(text)
            btn.setFixedSize(210, 100)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2f5a68;
                    color: white;
                    font-size: 30px;
                    font-weight: bold;
                    border-radius: 15px;
                }
                QPushButton:hover {
                    font-size: 33px;
                }
            """)
            return btn

        self.btn_mic = QPushButton()
        self.btn_mic.setFixedSize(100, 100)
        self.btn_mic.setIcon(QIcon(_get_image_path("mike.png")))
        self.btn_mic.setIconSize(QSize(55, 55))
        self.btn_mic.setStyleSheet("""
            QPushButton {
                background-color: #2f5a68;
                border-radius: 12px;
            }
        """)
        self.btn_mic.clicked.connect(self.toggle_mic_icon)
        self.btn_mic.enterEvent = lambda event: self.btn_mic.setIconSize(QSize(90, 90) if self.mic_on else QSize(65, 65))
        self.btn_mic.leaveEvent = lambda event: self.btn_mic.setIconSize(QSize(80, 80) if self.mic_on else QSize(55, 55))

        text_input = make_input_button("텍스트 입력")
        text_input_wrapper = QHBoxLayout()
        text_input_wrapper.addStretch(1)
        text_input_wrapper.addWidget(text_input)
        text_input_wrapper.addStretch(1)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(35)
        grid_layout.addWidget(make_invisible_button("사건개요", self.show_case_dialog), 0, 0)
        grid_layout.addWidget(make_invisible_button("검사측 증거품", self.show_prosecutor_evidence), 0, 1)
        grid_layout.addWidget(make_invisible_button("등장인물", self.show_profiles_dialog), 1, 0)
        grid_layout.addWidget(make_invisible_button("변호사측 증거품", self.show_attorney_evidence), 1, 1)
        grid_layout.addLayout(text_input_wrapper, 2, 0)
        grid_layout.addWidget(self.btn_mic, 2, 1, alignment=Qt.AlignCenter)

        btn_next = QPushButton("다음 단계로")
        btn_next.setStyleSheet(DEFAULT_BUTTON_STYLE)
        btn_next.setFixedWidth(220)
        btn_next.setMinimumHeight(40)
        btn_next.clicked.connect(self.proceed_to_next)

        button_block = QVBoxLayout()
        button_block.setSpacing(30)
        button_block.addLayout(grid_layout)
        button_block.addSpacing(40)
        button_block.addWidget(btn_next, alignment=Qt.AlignLeft)

        button_block_wrapper = QHBoxLayout()
        button_block_wrapper.addStretch(1)
        button_block_wrapper.addLayout(button_block)
        button_block_wrapper.addStretch(1)

        left = QVBoxLayout()
        left.setContentsMargins(40, 30, 20, 30)
        left.setSpacing(30)
        left.addLayout(title_wrapper)
        left.addStretch(1)
        left.addLayout(button_block_wrapper)
        left.addStretch(2)

        image_label = ResizableImage(_get_image_path("profile/Prosecutor.png"))
        image_label.setMaximumWidth(420)
        image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        right_layout = QVBoxLayout()
        right_layout.addStretch()
        right_layout.addWidget(image_label, alignment=Qt.AlignRight)
        right_layout.addStretch()

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(40, 30, 100, 30)
        main_layout.setSpacing(30)
        main_layout.addLayout(left, 3)
        main_layout.addLayout(right_layout, 2)

        self.setLayout(main_layout)

    def toggle_mic_icon(self):
        self.mic_on = not self.mic_on
        icon_path = "mike_on.png" if self.mic_on else "mike.png"
        size = QSize(80, 80) if self.mic_on else QSize(55, 55)
        self.btn_mic.setIcon(QIcon(_get_image_path(icon_path)))
        self.btn_mic.setIconSize(size)

    def proceed_to_next(self):
        if self.on_next:
            self.on_next()

    def show_case_dialog(self):
        # 인트로와 동일하게 피고/피해자/증인 정보는 제거
        lines = self.case_summary.strip().split('\n')
        filtered_lines = [
            line for line in lines
            if not any(tag in line for tag in ["[피고", "[피해자", "[증인1", "[증인2"])
        ]
        clean_text = "\n".join(filtered_lines)

        dlg = QMessageBox(self)
        dlg.setWindowTitle("사건 개요")
        dlg.setText(clean_text)
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.setMaximumSize(800, 500)
        dlg.setStyleSheet("QLabel { font-size: 14px; }")
        dlg.exec_()


    def show_profiles_dialog(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("등장인물 정보")
        dlg.setText(self.profiles)
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.setMaximumSize(800, 500)
        dlg.setStyleSheet("QLabel { font-size: 14px; }")
        dlg.exec_()

    def show_prosecutor_evidence(self):
        items = [f"{e.name}: {e.description[0]}" for e in self.evidences if e.type == "prosecutor"]
        text = "\n\n".join(items) if items else "검사측 증거물이 없습니다."
        QMessageBox.information(self, "검사측 증거품", text, QMessageBox.Ok)

    def show_attorney_evidence(self):
        items = [f"{e.name}: {e.description[0]}" for e in self.evidences if e.type == "attorney"]
        text = "\n\n".join(items) if items else "변호사측 증거물이 없습니다."
        QMessageBox.information(self, "변호사측 증거품", text, QMessageBox.Ok)