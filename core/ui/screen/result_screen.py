from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QTextEdit, QFrame, QVBoxLayout, QLabel, QPushButton,
    QSizePolicy, QApplication, QDialog
)
from PyQt5.QtCore import Qt, QTimer # Added QTimer
# from PyQt5.QtGui import QMovie # Not used directly, but QMovie could be an alternative for loading
import asyncio # Still needed for on_restart if it's async

from ..resizable_image import ResizableImage, _get_image_path, _get_profile_image_path
from ..style_constants import (
    DARK_BG_COLOR, WHITE_TEXT, PRIMARY_BLUE, # GREEN_BTN_COLOR, LIGHT_GRAY_TEXT, # Not used
    COMMON_PANEL_LABEL_STYLE
)
# Removed: from core.controller import get_judge_result_wrapper, CaseDataManager
# GameController interaction will be via signals handled by MainWindow


class LoadingDialog(QDialog):
    def __init__(self, message="로딩 중입니다...", parent=None):
        super().__init__(parent)
        self.setWindowTitle("로딩 중")
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint & ~Qt.WindowCloseButtonHint) # No close button
        self.setFixedSize(250, 120) # Slightly larger
        self.setStyleSheet(f"background-color: {DARK_BG_COLOR};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        self.message_label = QLabel(message) # Store for potential updates
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet(f"color: {WHITE_TEXT}; font-size: 16px;")

        layout.addWidget(self.message_label)
        # Optionally add a QProgressBar or a simple animation here
        # For simplicity, keeping it as text.

    def set_message(self, message):
        self.message_label.setText(message)
        QApplication.processEvents()


class ResultScreen(QWidget):
    def __init__(self, game_controller, on_restart_callback): # Added game_controller
        super().__init__()
        self.game_controller = game_controller
        self.on_restart_callback = on_restart_callback # Renamed from on_restart
        
        # These will be populated by MainWindow when setting up this screen,
        # or the screen can fetch initial parts from self.game_controller.case_data if available
        self.case_summary_data = ""
        self.profiles_data_text = "" # Store the text version of profiles for display if needed

        self.judgement_summary_text = ""
        self.case_truth_text = ""
        
        self.init_ui()

    def set_initial_data(self, summary: str, profiles_text: str):
        """Called by MainWindow to provide basic context if needed before verdict streams."""
        self.case_summary_data = summary
        self.profiles_data_text = profiles_text
        # self.result_text_display.setPlainText(
        #     f"[사건 요약]\n{summary}\n\n[등장인물]\n{profiles_text}\n\n판결 대기 중..."
        # )

    def init_ui(self):
        self.setStyleSheet(f"background-color: {DARK_BG_COLOR};") # Apply to self
        layout = QHBoxLayout(self) # Set layout on self
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

        right_layout = QVBoxLayout(right_frame) # Set layout on frame
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(20)

        label_ai_judge = QLabel("AI_판사")
        label_ai_judge.setStyleSheet(f"background-color: {PRIMARY_BLUE}; {COMMON_PANEL_LABEL_STYLE}")
        label_ai_judge.setAlignment(Qt.AlignCenter)

        self.result_image_label = ResizableImage(_get_profile_image_path, "judge.png")
        self.result_image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.retry_button = QPushButton("처음으로") # Stored as attribute
        self.retry_button.setStyleSheet(
            f"background-color: {PRIMARY_BLUE}; color: {WHITE_TEXT}; font-size: 18px; "
            "border-radius: 8px; padding: 12px;"
        )
        self.retry_button.setFixedHeight(50)
        self.retry_button.clicked.connect(self.handle_restart_clicked)
        self.retry_button.setEnabled(False) # Enable when results are fully loaded

        right_layout.addWidget(label_ai_judge, 0, Qt.AlignTop | Qt.AlignHCenter)
        right_layout.addSpacing(20)
        right_layout.addWidget(self.result_image_label, 1)
        right_layout.addSpacing(20)
        right_layout.addWidget(self.retry_button, 0, Qt.AlignBottom)
        # right_frame.setLayout(right_layout) # Already set

        layout.addWidget(self.result_text_display, 2)
        layout.addWidget(right_frame, 1)
        # self.setLayout(layout) # Already set


    def prepare_for_results(self):
        """Called by MainWindow when switching to this screen before verdict signals arrive."""
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
        QApplication.processEvents() # Update UI incrementally

    def finalize_judgement_summary(self):
        # Remove "..." from judgement summary if it was there
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
        # Remove "..." from truth text
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

        # The on_restart_callback is expected to be async from MainWindow's perspective
        # but here we just call it. MainWindow's restart_game_flow handles async.
        if self.on_restart_callback:
            # asyncio.ensure_future(self.on_restart_callback()) # MainWindow handles the async nature
            self.on_restart_callback() 
        
        # The loading dialog should be closed by MainWindow after restart prep is done,
        # or after a short delay if the callback is synchronous.
        # For simplicity, we can use a timer here if on_restart_callback is not directly closing it.
        QTimer.singleShot(1500, loading_dialog.accept) # Close after 1.5s as a fallback