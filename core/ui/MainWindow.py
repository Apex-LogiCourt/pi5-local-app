import sys
from PyQt5.QtWidgets import QMainWindow, QStackedWidget, QGraphicsOpacityEffect, QFrame
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QSequentialAnimationGroup, QParallelAnimationGroup, QTimer
from PyQt5.QtGui import QPalette, QColor


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

        self.red_border = QFrame(self)
        self.red_border.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: 10px solid rgba(255, 0, 0, 230);
            }
        """)
        self.red_border.setGeometry(0, 0, self.width(), self.height())
        self.red_border.hide()
        self.red_border.raise_()

    def add_page(self, page_name, page_widget):
        """페이지를 스택에 추가

        Args:
            page_name (str): 페이지 식별자 (예: "start", "generate", "prosecutor")
            page_widget (QWidget): 추가할 페이지 위젯
        """
        index = self.stacked_widget.addWidget(page_widget)
        self.page_indices[page_name] = index
        return index

    def switch_to_page(self, page_name, direction=None, objection=False):
        """특정 페이지로 전환

        Args:
            page_name (str): 전환할 페이지 식별자
            direction (str): 애니메이션 방향 ('left', 'right', None)
            objection (bool): 이의 있음! 효과 사용 여부
        """
        if page_name not in self.page_indices:
            print(f"경고: '{page_name}' 페이지를 찾을 수 없습니다.")
            return

        # 애니메이션 없이 전환
        if direction is None:
            index = self.page_indices[page_name]
            self.stacked_widget.setCurrentIndex(index)
            return

        # 이의 있음! 효과와 함께 전환
        if objection:
            self._animate_objection_switch(page_name, direction)
        else:
            # 일반 애니메이션과 함께 전환
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

    def _animate_objection_switch(self, page_name, direction):
        """이의 있음! 효과와 함께 페이지 전환 (흔들림 + 스와이프)

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
        height = self.stacked_widget.height()

        # 1단계: 흔들림 효과 (0.15초 - 3번 흔들림)
        shake_distance = 15  # 흔들림 거리 (픽셀)

        # 첫 번째 흔들림 (오른쪽)
        shake1 = QPropertyAnimation(current_widget, b"pos")
        shake1.setDuration(50)
        shake1.setStartValue(QPoint(0, 0))
        shake1.setEndValue(QPoint(shake_distance, 0))
        shake1.setEasingCurve(QEasingCurve.OutQuad)

        # 두 번째 흔들림 (왼쪽)
        shake2 = QPropertyAnimation(current_widget, b"pos")
        shake2.setDuration(50)
        shake2.setStartValue(QPoint(shake_distance, 0))
        shake2.setEndValue(QPoint(-shake_distance, 0))
        shake2.setEasingCurve(QEasingCurve.InOutQuad)

        # 세 번째 흔들림 (중앙으로)
        shake3 = QPropertyAnimation(current_widget, b"pos")
        shake3.setDuration(50)
        shake3.setStartValue(QPoint(-shake_distance, 0))
        shake3.setEndValue(QPoint(0, 0))
        shake3.setEasingCurve(QEasingCurve.InQuad)

        # 흔들림 시퀀스
        shake_sequence = QSequentialAnimationGroup()
        shake_sequence.addAnimation(shake1)
        shake_sequence.addAnimation(shake2)
        shake_sequence.addAnimation(shake3)

        # 2단계: 빠른 스와이프 (0.2초)
        # 방향에 따라 시작/종료 위치 설정
        if direction == 'right':
            current_end = QPoint(width, 0)
            next_start = QPoint(-width, 0)
        else:  # 'left'
            current_end = QPoint(-width, 0)
            next_start = QPoint(width, 0)

        next_end = QPoint(0, 0)

        # 다음 위젯 준비
        next_widget.setGeometry(0, 0, width, height)
        next_widget.move(next_start)
        next_widget.show()
        next_widget.raise_()

        # 현재 위젯 스와이프 아웃
        swipe_out_anim = QPropertyAnimation(current_widget, b"pos")
        swipe_out_anim.setDuration(200)
        swipe_out_anim.setStartValue(QPoint(0, 0))
        swipe_out_anim.setEndValue(current_end)
        swipe_out_anim.setEasingCurve(QEasingCurve.InCubic)  # 더 빠르게

        # 다음 위젯 스와이프 인
        swipe_in_anim = QPropertyAnimation(next_widget, b"pos")
        swipe_in_anim.setDuration(200)
        swipe_in_anim.setStartValue(next_start)
        swipe_in_anim.setEndValue(next_end)
        swipe_in_anim.setEasingCurve(QEasingCurve.OutCubic)  # 더 빠르게

        # 2단계 애니메이션 그룹
        swipe_group = QParallelAnimationGroup()
        swipe_group.addAnimation(swipe_out_anim)
        swipe_group.addAnimation(swipe_in_anim)

        # 전체 시퀀스 (흔들림 -> 스와이프)
        sequence = QSequentialAnimationGroup()
        sequence.addAnimation(shake_sequence)
        sequence.addAnimation(swipe_group)

        # 애니메이션 완료 시 처리
        def on_objection_finished():
            self.stacked_widget.setCurrentIndex(next_index)
            current_widget.move(0, 0)
            self.current_animation = None

        sequence.finished.connect(on_objection_finished)

        # 애니메이션 시작
        self.current_animation = sequence
        self.objection_swipe_out = swipe_out_anim  # 참조 유지
        self.objection_swipe_in = swipe_in_anim
        sequence.start()

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

    def show_red_border_flash(self, duration_ms=3000):
        self.red_border.setGeometry(0, 0, self.width(), self.height())
        self.red_border.show()
        self.red_border.raise_()

        opacity_effect = QGraphicsOpacityEffect()
        self.red_border.setGraphicsEffect(opacity_effect)

        blink_cycle = 500
        num_blinks = int(duration_ms / blink_cycle)

        sequence = QSequentialAnimationGroup()

        for i in range(num_blinks):
            fade_in = QPropertyAnimation(opacity_effect, b"opacity")
            fade_in.setDuration(200)
            fade_in.setStartValue(0.3)
            fade_in.setEndValue(1.0)
            fade_in.setEasingCurve(QEasingCurve.InOutQuad)

            fade_out = QPropertyAnimation(opacity_effect, b"opacity")
            fade_out.setDuration(200)
            fade_out.setStartValue(1.0)
            fade_out.setEndValue(0.3)
            fade_out.setEasingCurve(QEasingCurve.InOutQuad)

            sequence.addAnimation(fade_in)
            sequence.addAnimation(fade_out)

        final_fade_out = QPropertyAnimation(opacity_effect, b"opacity")
        final_fade_out.setDuration(300)
        final_fade_out.setStartValue(0.3)
        final_fade_out.setEndValue(0.0)
        final_fade_out.setEasingCurve(QEasingCurve.InQuad)
        sequence.addAnimation(final_fade_out)

        def on_finished():
            self.red_border.hide()
            self.red_border.setGraphicsEffect(None)

        sequence.finished.connect(on_finished)
        sequence.start()

        self.border_animation = sequence

    def resizeEvent(self, event):
        """윈도우 크기 변경 시 빨간색 테두리도 조정"""
        super().resizeEvent(event)
        if hasattr(self, 'red_border'):
            self.red_border.setGeometry(0, 0, self.width(), self.height())
