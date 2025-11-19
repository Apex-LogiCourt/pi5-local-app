import sys
from PyQt5.QtWidgets import QMainWindow, QStackedWidget
from PyQt5.QtCore import Qt


class MainWindow(QMainWindow):
    """메인 윈도우 - QStackedWidget으로 페이지 전환 관리"""

    def __init__(self):
        super().__init__()
        self._setup_window()
        self._setup_stacked_widget()

    def _setup_window(self):
        """윈도우 기본 설정"""
        self.setWindowTitle("로직코트")
        # 배경색 설정
        self.setStyleSheet("QMainWindow { background-color: rgb(15, 39, 72); }")
        # 최소 크기 설정 (UI가 너무 작아지지 않도록)
        self.setMinimumSize(1280, 720)
        # 전체화면으로 시작
        # self.showFullScreen()

    def _setup_stacked_widget(self):
        """StackedWidget 초기화"""
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # 페이지 인덱스를 저장할 딕셔너리
        self.page_indices = {}

    def add_page(self, page_name, page_widget):
        """페이지를 스택에 추가

        Args:
            page_name (str): 페이지 식별자 (예: "start", "generate", "prosecutor")
            page_widget (QWidget): 추가할 페이지 위젯
        """
        index = self.stacked_widget.addWidget(page_widget)
        self.page_indices[page_name] = index
        return index

    def switch_to_page(self, page_name):
        """특정 페이지로 전환

        Args:
            page_name (str): 전환할 페이지 식별자
        """
        if page_name in self.page_indices:
            index = self.page_indices[page_name]
            self.stacked_widget.setCurrentIndex(index)
        else:
            print(f"경고: '{page_name}' 페이지를 찾을 수 없습니다.")

    def get_current_page(self):
        """현재 표시중인 페이지 위젯 반환"""
        return self.stacked_widget.currentWidget()

    def get_page_by_name(self, page_name):
        """페이지 이름으로 페이지 위젯 가져오기

        Args:
            page_name (str): 페이지 식별자

        Returns:
            QWidget: 해당 페이지 위젯 또는 None
        """
        if page_name in self.page_indices:
            index = self.page_indices[page_name]
            return self.stacked_widget.widget(index)
        return None
