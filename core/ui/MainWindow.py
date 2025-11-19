import sys
from PyQt5.QtWidgets import QMainWindow, QStackedWidget
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint


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
        self.showFullScreen()

    def _setup_stacked_widget(self):
        """StackedWidget 초기화"""
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # 페이지 인덱스를 저장할 딕셔너리
        self.page_indices = {}

        # 애니메이션 변수
        self.current_animation = None

    def add_page(self, page_name, page_widget):
        """페이지를 스택에 추가

        Args:
            page_name (str): 페이지 식별자 (예: "start", "generate", "prosecutor")
            page_widget (QWidget): 추가할 페이지 위젯
        """
        index = self.stacked_widget.addWidget(page_widget)
        self.page_indices[page_name] = index
        return index

    def switch_to_page(self, page_name, direction=None):
        """특정 페이지로 전환

        Args:
            page_name (str): 전환할 페이지 식별자
            direction (str): 애니메이션 방향 ('left', 'right', None)
        """
        if page_name not in self.page_indices:
            print(f"경고: '{page_name}' 페이지를 찾을 수 없습니다.")
            return

        # 애니메이션 없이 전환
        if direction is None:
            index = self.page_indices[page_name]
            self.stacked_widget.setCurrentIndex(index)
            return

        # 애니메이션과 함께 전환
        self._animate_page_switch(page_name, direction)

    def _animate_page_switch(self, page_name, direction):
        """페이지 전환 애니메이션

        Args:
            page_name (str): 전환할 페이지 식별자
            direction (str): 'left' 또는 'right'
        """
        if self.current_animation and self.current_animation.state() == QPropertyAnimation.Running:
            return  # 이미 애니메이션 실행 중이면 무시

        current_widget = self.stacked_widget.currentWidget()
        next_index = self.page_indices[page_name]
        next_widget = self.stacked_widget.widget(next_index)

        if current_widget is None or next_widget is None:
            self.stacked_widget.setCurrentIndex(next_index)
            return

        width = self.stacked_widget.width()

        # 방향에 따라 시작/종료 위치 설정
        if direction == 'right':
            # 오른쪽으로 스와이프 (검사 -> 변호사)
            current_end = QPoint(width, 0)
            next_start = QPoint(-width, 0)
        else:  # 'left'
            # 왼쪽으로 스와이프 (변호사 -> 검사)
            current_end = QPoint(-width, 0)
            next_start = QPoint(width, 0)

        next_end = QPoint(0, 0)

        # 다음 위젯 준비
        next_widget.setGeometry(0, 0, width, self.stacked_widget.height())
        next_widget.move(next_start)
        next_widget.show()
        next_widget.raise_()

        # 현재 위젯 애니메이션
        self.current_anim_out = QPropertyAnimation(current_widget, b"pos")
        self.current_anim_out.setDuration(300)
        self.current_anim_out.setStartValue(QPoint(0, 0))
        self.current_anim_out.setEndValue(current_end)
        self.current_anim_out.setEasingCurve(QEasingCurve.InOutQuad)

        # 다음 위젯 애니메이션
        self.current_anim_in = QPropertyAnimation(next_widget, b"pos")
        self.current_anim_in.setDuration(300)
        self.current_anim_in.setStartValue(next_start)
        self.current_anim_in.setEndValue(next_end)
        self.current_anim_in.setEasingCurve(QEasingCurve.InOutQuad)

        # 애니메이션 완료 시 처리
        def on_animation_finished():
            self.stacked_widget.setCurrentIndex(next_index)
            current_widget.move(0, 0)
            self.current_animation = None

        self.current_anim_in.finished.connect(on_animation_finished)

        # 애니메이션 시작
        self.current_animation = self.current_anim_in
        self.current_anim_out.start()
        self.current_anim_in.start()

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
