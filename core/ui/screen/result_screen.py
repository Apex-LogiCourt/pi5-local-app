from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QTextEdit, QFrame, QVBoxLayout, QLabel, QPushButton,
    QSizePolicy, QApplication, QDialog
)
from PyQt5.QtGui import QPixmap # QPixmap 직접 사용을 위해 import
from PyQt5.QtCore import Qt, QTimer
import asyncio

# from ui.resizable_image import ResizableImage, _get_image_path, _get_profile_image_path # 이 줄은 제거
from ui.style_constants import (
    DARK_BG_COLOR, WHITE_TEXT, PRIMARY_BLUE,
    COMMON_PANEL_LABEL_STYLE
)
# import os # 직접 경로 문자열 사용 시 이 파일에서 os 모듈이 필수는 아님

class LoadingDialog(QDialog):
    def __init__(self, message="로딩 중입니다...", parent=None):
        super().__init__(parent)
        self.setWindowTitle("로딩 중")
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint & ~Qt.WindowCloseButtonHint)
        self.setFixedSize(250, 120)
        self.setStyleSheet(f"background-color: {DARK_BG_COLOR};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        self.message_label = QLabel(message)
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet(f"color: {WHITE_TEXT}; font-size: 16px;")

        layout.addWidget(self.message_label)

    def set_message(self, message):
        self.message_label.setText(message)
        QApplication.processEvents()


class ResultScreen(QWidget):
    def __init__(self, game_controller, on_restart_callback):
        super().__init__()
        self.game_controller = game_controller
        self.on_restart_callback = on_restart_callback
        
        self.case_summary_data = ""
        self.profiles_data_text = ""

        self.judgement_summary_text = ""
        self.case_truth_text = ""
        
        self.init_ui()

    def set_initial_data(self, summary: str, profiles_text: str):
        self.case_summary_data = summary
        self.profiles_data_text = profiles_text

    def init_ui(self):
        self.setStyleSheet(f"background-color: {DARK_BG_COLOR};")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.result_text_display = QTextEdit()
        self.result_text_display.setReadOnly(True)
        self.result_text_display.setStyleSheet(
            f"background-color: {DARK_BG_COLOR}; color: {WHITE_TEXT}; font-size: 16px; "
            "padding: 15px; border: none;"
        )
        self.result_text_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.result_text_display.setPlaceholderText("AI 판사의 판결을 기다립니다...")

        right_frame = QFrame()
        right_frame.setStyleSheet(f"background-color: {DARK_BG_COLOR}; border-left: 1px solid #444;")
        right_frame.setFixedWidth(400)

        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(20)

        label_ai_judge = QLabel("AI_판사")
        label_ai_judge.setStyleSheet(f"background-color: {PRIMARY_BLUE}; {COMMON_PANEL_LABEL_STYLE}")
        label_ai_judge.setAlignment(Qt.AlignCenter)

        # --- 판사 이미지 로드 방식 변경 ---
        judge_image_path = "core/assets/profile/judge.png" # 직접 경로 문자열 사용
        
        image_pixmap = QPixmap(judge_image_path)
        self.result_image_label = QLabel() # 표준 QLabel 사용

        if image_pixmap.isNull():
            print(f"오류: 판사 이미지를 불러올 수 없습니다 - {judge_image_path}")
            self.result_image_label.setText("판사 이미지\n로드 실패")
        else:
            # QLabel에 이미지를 표시 (setScaledContents(True) 또는 직접 스케일링)
            # 여기서는 setScaledContents(True)를 사용하여 QLabel 크기에 맞춰 자동 스케일링하도록 함
            # 원본 ResizableImage는 setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)를 가졌었음
            self.result_image_label.setPixmap(image_pixmap)
            self.result_image_label.setScaledContents(True) # QLabel 크기에 맞춰 이미지 스케일링

        self.result_image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # 크기 정책 유지
        self.result_image_label.setAlignment(Qt.AlignCenter) # 중앙 정렬 추가
        # --- 이미지 처리 수정 완료 ---

        self.retry_button = QPushButton("처음으로")
        self.retry_button.setStyleSheet(
            f"background-color: {PRIMARY_BLUE}; color: {WHITE_TEXT}; font-size: 18px; "
            "border-radius: 8px; padding: 12px;"
        )
        self.retry_button.setFixedHeight(50)
        self.retry_button.clicked.connect(self.handle_restart_clicked)
        self.retry_button.setEnabled(False)

        right_layout.addWidget(label_ai_judge, 0, Qt.AlignTop | Qt.AlignHCenter)
        right_layout.addSpacing(20)
        right_layout.addWidget(self.result_image_label, 1)
        right_layout.addSpacing(20)
        right_layout.addWidget(self.retry_button, 0, Qt.AlignBottom)

        layout.addWidget(self.result_text_display, 2)
        layout.addWidget(right_frame, 1)

    def prepare_for_results(self):
        self.judgement_summary_text = "🧑‍⚖️ AI 판결 요약:\n"
        self.case_truth_text = "\n\n🕵️ 사건의 진실:\n"
        self.result_text_display.setPlainText(
            self.judgement_summary_text + "...\n" + self.case_truth_text + "..."
        )
        self.retry_button.setEnabled(False)
        QApplication.processEvents()

    def append_judgement_chunk(self, chunk: str):
        self.judgement_summary_text += chunk
        self.result_text_display.setPlainText(
            self.judgement_summary_text + "...\n" + self.case_truth_text + "..."
        )
        QApplication.processEvents()

    def finalize_judgement_summary(self):
        if self.judgement_summary_text.endswith("..."):
            self.judgement_summary_text = self.judgement_summary_text[:-3]
        self.result_text_display.setPlainText(
            self.judgement_summary_text.strip() + "\n" + self.case_truth_text + "..."
        )
        QApplication.processEvents()

    def append_truth_chunk(self, chunk: str):
        self.case_truth_text += chunk
        self.result_text_display.setPlainText(
            self.judgement_summary_text.strip() + "\n" + self.case_truth_text + "..."
        )
        QApplication.processEvents()

    def finalize_results(self):
        if self.case_truth_text.endswith("..."):
            self.case_truth_text = self.case_truth_text[:-3]
        self.result_text_display.setPlainText(
            self.judgement_summary_text.strip() + "\n" + self.case_truth_text.strip()
        )
        self.retry_button.setEnabled(True)
        QApplication.processEvents()

    def display_error(self, error_message: str):
        self.result_text_display.setPlainText(f"⚠️ 판결 생성 중 오류가 발생했습니다:\n{error_message}")
        self.retry_button.setEnabled(True)

    def handle_restart_clicked(self):
        loading_dialog = LoadingDialog(parent=self)
        loading_dialog.show()
        QApplication.processEvents()

        if self.on_restart_callback:
            self.on_restart_callback() 
        
        QTimer.singleShot(1500, loading_dialog.accept)