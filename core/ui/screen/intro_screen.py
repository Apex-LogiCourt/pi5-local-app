from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QSizePolicy, QFrame
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
# import os # 직접 경로 문자열 사용 시 필수는 아님

from ui.style_constants import (
    DARK_BG_COLOR, SECONDARY_BLUE, COMMON_PANEL_LABEL_STYLE,
    DEFAULT_BUTTON_STYLE, TEXT_EDIT_STYLE_TRANSPARENT_BG, WHITE_TEXT,
    HTML_H3_STYLE, HTML_P_STYLE, HTML_LI_STYLE
)
# from ui.resizable_image import _get_image_path, _get_profile_image_path # 이 줄은 제거
import re

# 한글 이름을 영문 파일명으로 매핑
KOREAN_TO_ENGLISH_MAP = {
    "은영": "Eunyoung", "봄달": "Bomdal", "지훈": "Jihoon", "소현": "Sohyun",
    "영화": "Younghwa", "성일": "Sungil", "기효": "Kihyo", "승표": "Seungpyo",
    "주안": "Jooahn", "선희": "Sunhee", "민영": "Minyoung", "상도": "Sangdo",
    "기서": "Kiseo", "원탁": "Wontak", "이안": "Ian", "판사": "judge"
}

# 제목 문자열에서 이름 추출
def extract_name_from_title(title: str) -> str:
    match = re.search(r"이름\s*:\s*(\S+)", title)
    if match:
        full_name = match.group(1)
        if len(full_name) > 2 and full_name[0] in ['김', '이', '박', '최', '정', '강', '조', '윤', '장', '임', '오', '한', '신', '서', '권', '황', '안', '송', '유', '홍']:
            return full_name[1:]
        return full_name
    return ""

# 이름에 해당하는 프로필 이미지 QLabel 생성 함수 수정: 직접 경로 사용
def get_profile_image_label(name: str) -> QLabel:
    label = QLabel()
    try:
        romanized = KOREAN_TO_ENGLISH_MAP.get(name)
        if not romanized and len(name) >= 2 and name != "판사":
            if name[0] in ['김', '이', '박', '최', '정', '강', '조', '윤', '장', '임', '오', '한', '신', '서', '권', '황', '안', '송', '유', '홍'] and len(name) > 1:
                romanized = KOREAN_TO_ENGLISH_MAP.get(name[1:])

        if romanized:
            # 직접 경로 문자열 사용 (프로젝트 루트 기준)
            img_path = f"core/assets/profile/{romanized}.png"
            pix = QPixmap(img_path)
            if pix.isNull():
                print(f"Warning: Profile image failed to load: {img_path} for name {name} (romanized: {romanized})")
                label.setText(f"{name}\n(이미지 로드 실패)")
            else:
                label.setPixmap(pix)
        else:
            label.setText(f"{name}\n(이미지 없음)")
    except Exception as e:
        print(f"Error getting profile image for {name}: {e}")
        label.setText(f"{name}\n(이미지 오류)")
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet(f"color: {WHITE_TEXT};")
    return label

class IntroScreen(QWidget):
    def __init__(self, game_controller, on_intro_finished_callback,
                 summary_text: str, profiles_data: list, evidences_data: list):
        super().__init__()
        self.game_controller = game_controller
        self.on_intro_finished = on_intro_finished_callback

        self.case_summary = summary_text
        self.profiles_list = profiles_data
        self.evidences = evidences_data

        self.current_block_index = -1
        self.display_blocks = []
        self.image_blocks = [] # QLabel 객체들이 저장됨

        self._prepare_display_blocks()
        self.init_ui()
        self.show_next_block()

    def _prepare_display_blocks(self):
        title_html = f"<h3 style='{HTML_H3_STYLE}'>사건개요</h3>"
        lines = [ln.strip() for ln in self.case_summary.split('\n')
                 if ln.strip() and not any(tag in ln for tag in ["[피고", "[피해자", "[증인1", "[증인2"])]
        content_html = ''.join(f"<p style='{HTML_P_STYLE}'>{ln}</p>" for ln in lines)

        proc_ev = [e['name'] for e in self.evidences if e['type'] == 'prosecutor']
        att_ev = [e['name'] for e in self.evidences if e['type'] == 'attorney']

        evidence_html = ""
        if proc_ev:
            evidence_html += (f"<h3 style='{HTML_H3_STYLE}'>검사측 증거물</h3><ul>" +
                              ''.join(f"<li style='{HTML_LI_STYLE}'>{i}</li>" for i in proc_ev) + "</ul>")
        if att_ev:
            evidence_html += (f"<h3 style='{HTML_H3_STYLE}'>변호사측 증거물</h3><ul>" +
                               ''.join(f"<li style='{HTML_LI_STYLE}'>{i}</li>" for i in att_ev) + "</ul>")

        self.display_blocks.append(title_html + content_html + evidence_html)
        # get_profile_image_label 함수는 이미 직접 경로를 사용하도록 수정됨
        self.image_blocks.append(get_profile_image_label("판사"))


        type_map = {"defendant": "피고", "victim": "피해자", "witness": "목격자", "reference": "참고인"}
        for p_info in self.profiles_list:
            name = p_info.get('name', '정보 없음')
            role = type_map.get(p_info.get('type'), p_info.get('type', '정보 없음'))
            gender = p_info.get('gender', '정보 없음')
            age = p_info.get('age', '정보 없음')
            context = p_info.get('context', '정보 없음')

            head = f"이름: {name} ({role})"
            head_html = f"<h3 style='{HTML_H3_STYLE}'>{head}</h3>"
            body_html = f"<p style='{HTML_P_STYLE}'>성별: {gender}, 나이: {age}세</p>"
            context_lines = context.split('\n')
            bullets = [ln.lstrip('- ').strip() for ln in context_lines if ln.strip().startswith('-')]
            paras = [ln for ln in context_lines if not ln.strip().startswith('-') and ln.strip()]
            if bullets:
                body_html += '<ul>' + ''.join(f"<li style='{HTML_LI_STYLE}'>{b}</li>" for b in bullets) + '</ul>'
            body_html += ''.join(f"<p style='{HTML_P_STYLE}'>{p}</p>" for p in paras)

            self.display_blocks.append(head_html + body_html)
            
            base_name_for_image = extract_name_from_title(head)
            if not base_name_for_image: base_name_for_image = name
            # get_profile_image_label 함수는 이미 직접 경로를 사용하도록 수정됨
            self.image_blocks.append(get_profile_image_label(base_name_for_image))


    def init_ui(self):
        self.setStyleSheet(f"background-color: {DARK_BG_COLOR};")
        style = (
            f"QTextEdit {{ {TEXT_EDIT_STYLE_TRANSPARENT_BG} }}"
            f"QPushButton {{ {DEFAULT_BUTTON_STYLE} }}"
            f"QLabel {{ color: {WHITE_TEXT}; background-color: transparent; }}"
        )
        self.setStyleSheet(self.styleSheet() + style)

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(40)

        left = QVBoxLayout()
        hdr = QHBoxLayout()
        hdr.addStretch()
        self.label_section = QLabel("사건설명")
        self.label_section.setFixedWidth(200)
        self.label_section.setAlignment(Qt.AlignCenter)
        self.label_section.setStyleSheet(f"background-color: {SECONDARY_BLUE}; {COMMON_PANEL_LABEL_STYLE}")
        hdr.addWidget(self.label_section)
        hdr.addStretch()
        left.addLayout(hdr)

        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        left.addWidget(self.text_display, 1)

        self.next_button = QPushButton("다음")
        self.next_button.setFixedHeight(50)
        self.next_button.clicked.connect(self.show_next_block)
        left.addWidget(self.next_button, alignment=Qt.AlignRight)

        right_frame = QFrame()
        # 배경 이미지 경로 직접 지정 (프로젝트 루트 기준)
        # Qt 스타일시트에서 url()은 보통 실행 디렉토리 기준이거나 절대경로를 사용합니다.
        # "core/assets/background1.png"가 작동하려면 CWD가 프로젝트 루트여야 합니다.
        background_image_path = "core/assets/background1.png"
        # QPixmap으로 로드하여 스타일시트에 직접 설정하는 대신, 
        # QFrame의 배경으로 설정할 때는 url()을 사용해야 합니다.
        # 경로에 공백이나 특수문자가 없다면 replace는 필수는 아닐 수 있습니다.
        # Qt는 url() 내에서 '/'를 경로 구분자로 선호합니다.
        right_frame.setStyleSheet(
            f"background-image: url({background_image_path});"
            "background-repeat: no-repeat;"
            "background-position: center;"
            "background-size: cover;"
            "border-radius: 10px;"
        )
        # 만약 위 스타일시트가 이미지를 못 찾는다면, QPixmap으로 로드 후 QFrame을 상속받는 커스텀 위젯에서
        # paintEvent를 오버라이드하여 직접 그리는 방법도 고려할 수 있습니다.
        # 또는, QLabel을 배경으로 사용하는 방법도 있습니다.
        # QLabel 배경 예시:
        # self.background_label_for_frame = QLabel(right_frame)
        # bg_pix = QPixmap(background_image_path)
        # if not bg_pix.isNull():
        #     self.background_label_for_frame.setPixmap(bg_pix.scaled(right_frame.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        #     self.background_label_for_frame.lower() # 다른 위젯들 뒤로 보내기
        # right_frame.layout().addWidget(self.background_label_for_frame) # right_frame에 레이아웃이 먼저 설정되어야 함.

        right_layout = QVBoxLayout(right_frame) # 이 레이아웃이 right_frame에 적용됨
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(0)

        self.image_label_container = QFrame()
        self.image_label_container.setStyleSheet("background-color: transparent;")
        container_layout = QVBoxLayout(self.image_label_container)
        container_layout.setContentsMargins(0,0,0,0)
        
        self.image_label = QLabel() # 프로필 이미지가 표시될 라벨
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(True) 
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setMinimumSize(200, 200)
        container_layout.addWidget(self.image_label)

        right_layout.addWidget(self.image_label_container, 1)

        self.main_layout.addLayout(left, 3)
        self.main_layout.addWidget(right_frame, 2)

    def show_next_block(self):
        self.current_block_index += 1
        if self.current_block_index < len(self.display_blocks):
            self.text_display.setHtml(self.display_blocks[self.current_block_index])

            if self.current_block_index == 0:
                self.label_section.setText("사건 개요")
            else:
                html_content = self.display_blocks[self.current_block_index]
                match = re.search(r"<h3[^>]*>(.*?)<\/h3>", html_content, re.IGNORECASE)
                if match:
                    title_text = match.group(1)
                    name_match = re.search(r"이름\s*:\s*(\S+)\s*\((\S+)\)", title_text)
                    if name_match:
                        self.label_section.setText(f"{name_match.group(2)}: {name_match.group(1)}")
                    else:
                        self.label_section.setText(title_text[:15])
                else:
                    self.label_section.setText(f"정보 #{self.current_block_index + 1}")

            # image_blocks에는 get_profile_image_label로 생성된 QLabel들이 들어있음
            img_widget_template = self.image_blocks[self.current_block_index]
            if img_widget_template and img_widget_template.pixmap() and not img_widget_template.pixmap().isNull():
                # self.image_label의 현재 크기에 맞춰 스케일링
                # self.image_label.setScaledContents(True)를 사용하고 있으므로,
                # pixmap만 설정해도 self.image_label 크기에 맞춰질 것입니다.
                # 다만, 더 나은 품질이나 비율 유지를 위해 여기서 한 번 더 스케일링 할 수 있습니다.
                # 여기서는 image_label_container의 크기가 유동적이므로,
                # image_label에 pixmap을 설정하고 setScaledContents(True)에 의존합니다.
                # 또는, 명시적으로 scaled pixmap을 설정할 수 있습니다.
                scaled_pixmap = img_widget_template.pixmap().scaled(
                    self.image_label.size(), 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                if not scaled_pixmap.isNull() and scaled_pixmap.width() > 1 and scaled_pixmap.height() > 1 : # 유효한 크기인지 확인
                     self.image_label.setPixmap(scaled_pixmap)
                else: # 스케일링 실패 또는 매우 작은 크기면 원본 pixmap 사용 (setScaledContents가 처리)
                     self.image_label.setPixmap(img_widget_template.pixmap())

            else:
                self.image_label.clear()
                self.image_label.setText(img_widget_template.text() if img_widget_template else "이미지 없음")

            is_last = self.current_block_index == len(self.display_blocks) - 1
            self.next_button.setText("재판 시작" if is_last else "다음")
        else:
            if self.on_intro_finished:
                self.on_intro_finished()