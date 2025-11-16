from PyQt5.QtCore import QObject, QTimer


class Typewriter(QObject):
    def __init__(self, update_fn, char_interval=30, sentence_pause=1000, parent=None):
        """
        update_fn: 텍스트를 실제로 화면에 뿌리는 함수 (ex. label.setText, Window.update_profile_text_label)
        char_interval: 글자 하나 찍는 간격 (ms)
        sentence_pause: 한 문장 다 찍고 다음 문장 시작하기 전 쉬는 시간 (ms)
        """
        super().__init__(parent)
        self.update_fn = update_fn

        self.char_interval = char_interval
        self.sentence_pause = sentence_pause

        self.queue = []          # 들어온 문장들
        self.current_text = ""   # 지금 타이핑 중인 문장
        self.index = 0
        self.is_typing = False

        # 글자 하나씩 찍는 타이머
        self.char_timer = QTimer(self)
        self.char_timer.timeout.connect(self._type_next_char)

        # 한 문장 끝난 뒤 쉬는 타이머
        self.pause_timer = QTimer(self)
        self.pause_timer.setSingleShot(True)
        self.pause_timer.timeout.connect(self._start_next_message)

    def enqueue(self, text: str):
        """문장 추가만 해주면 됨. 나머지는 알아서 처리."""
        if not isinstance(text, str):
            text = str(text)

        self.queue.append(text)

        # 지금 아무 것도 안 치고 있으면 바로 시작
        if not self.is_typing:
            self._start_next_message()

    def _start_next_message(self):
        if not self.queue:
            self.is_typing = False
            return

        self.is_typing = True
        self.current_text = self.queue.pop(0)
        self.index = 0

        # 새 문장 시작할 때 일단 비우고 시작하고 싶으면 이 줄 살리기
        self.update_fn("")

        self.char_timer.start(self.char_interval)

    def _type_next_char(self):
        if self.index >= len(self.current_text):
            # 문장 끝
            self.char_timer.stop()
            # 문장 사이 잠깐 쉬었다가 다음 문장
            self.pause_timer.start(self.sentence_pause)
            return

        partial = self.current_text[: self.index + 1]
        self.update_fn(partial)
        self.index += 1

    # 선택: 지금 치는 거 바로 끝내고 전체 문장 찍어버리기 (스킵용)
    def skip_current(self):
        if not self.is_typing:
            return
        self.char_timer.stop()
        self.update_fn(self.current_text)
        self.pause_timer.start(self.sentence_pause)
