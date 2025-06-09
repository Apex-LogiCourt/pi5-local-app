from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QSizePolicy, QFrame
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from ui.style_constants import (
    DARK_BG_COLOR, SECONDARY_BLUE, COMMON_PANEL_LABEL_STYLE,
    DEFAULT_BUTTON_STYLE, TEXT_EDIT_STYLE_TRANSPARENT_BG, WHITE_TEXT,
    HTML_H3_STYLE, HTML_P_STYLE, HTML_LI_STYLE
)
# Assuming resizable_image.py is in the parent directory 'ui'
from ui.resizable_image import _get_image_path, _get_profile_image_path
# Removed: from core.data_models import Evidence (data will be passed)
import re

# 한글 이름을 영문 파일명으로 매핑 (can be moved to a utils file if shared more)
KOREAN_TO_ENGLISH_MAP = {
    "은영": "Eunyoung", "봄달": "Bomdal", "지훈": "Jihoon", "소현": "Sohyun",
    "영화": "Younghwa", "성일": "Sungil", "기효": "Kihyo", "승표": "Seungpyo",
    "주안": "Jooahn", "선희": "Sunhee", "민영": "Minyoung", "상도": "Sangdo",
    "기서": "Kiseo", "원탁": "Wontak", "이안": "Ian", "판사": "judge" # Added judge
}

# 제목 문자열에서 이름 추출
def extract_name_from_title(title: str) -> str:
    match = re.search(r"이름\s*:\s*(\S+)", title)
    if match:
        full_name = match.group(1)
        # Handle cases like "김소현" -> "소현", "소현" -> "소현"
        if len(full_name) > 2 and full_name[0] in ['김', '이', '박', '최', '정', '강', '조', '윤', '장', '임', '오', '한', '신', '서', '권', '황', '안', '송', '유', '홍']:
            return full_name[1:]
        return full_name
    return ""

# 이름에 해당하는 프로필 이미지 QLabel 생성
def get_profile_image_label(name: str) -> QLabel:
    label = QLabel()
    try:
        # Use the mapping directly, extract_name_from_title should give the base name
        romanized = KOREAN_TO_ENGLISH_MAP.get(name)
        if not romanized and len(name) >= 2 and name != "판사": # Special handling if name could be "김은영"
            # Try stripping common surnames if not found directly
            if name[0] in ['김', '이', '박', '최', '정', '강', '조', '윤', '장', '임', '오', '한', '신', '서', '권', '황', '안', '송', '유', '홍'] and len(name) > 1:
                romanized = KOREAN_TO_ENGLISH_MAP.get(name[1:])

        if romanized:
            # _get_profile_image_path expects only the filename
            img_path = _get_profile_image_path(f"{romanized}.png")
            pix = QPixmap(img_path)
            if pix.isNull():
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

        # Data is now passed directly
        self.case_summary = summary_text
        self.profiles_list = profiles_data # Expects list of profile objects/dicts
        self.evidences = evidences_data # Expects list of evidence objects/dicts

        self.current_block_index = -1
        self.display_blocks = []
        self.image_blocks = [] # Will store QLabels with QPixmaps

        self._prepare_display_blocks()
        self.init_ui()
        self.show_next_block()

    def _prepare_display_blocks(self):
        # 1) 사건개요 + 증거목록 HTML
        title_html = f"<h3 style='{HTML_H3_STYLE}'>사건개요</h3>"
        # Assuming self.case_summary is a plain string outline
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
        # Image for summary/evidence can be a generic judge or court image
        self.image_blocks.append(get_profile_image_label("판사"))


        # 2) 등장인물 정보 + 프로필 이미지
        # profiles_list is assumed to be a list of dicts/objects like:
        # [{'name': '김민준', 'type': '피고', 'gender': '남성', 'age': 30, 'context': '사건의 중심에 있는 인물...'}, ...]
        type_map = {"defendant": "피고", "victim": "피해자", "witness": "목격자", "reference": "참고인"}

        for p_info in self.profiles_list:
            name = p_info.get('name', '정보 없음')
            role = type_map.get(p_info.get('type'), p_info.get('type', '정보 없음'))
            gender = p_info.get('gender', '정보 없음')
            age = p_info.get('age', '정보 없음')
            context = p_info.get('context', '정보 없음')

            head = f"이름: {name} ({role})" # This is the format extract_name_from_title expects somewhat
            head_html = f"<h3 style='{HTML_H3_STYLE}'>{head}</h3>"

            body_html = f"<p style='{HTML_P_STYLE}'>성별: {gender}, 나이: {age}세</p>"
            # Assuming context might have bullet points
            context_lines = context.split('\n')
            bullets = [ln.lstrip('- ').strip() for ln in context_lines if ln.strip().startswith('-')]
            paras = [ln for ln in context_lines if not ln.strip().startswith('-') and ln.strip()]

            if bullets:
                body_html += '<ul>' + ''.join(f"<li style='{HTML_LI_STYLE}'>{b}</li>" for b in bullets) + '</ul>'
            body_html += ''.join(f"<p style='{HTML_P_STYLE}'>{p}</p>" for p in paras)

            self.display_blocks.append(head_html + body_html)
            
            # Extract base name for image mapping
            base_name_for_image = extract_name_from_title(head) # e.g. "김소현" -> "소현"
            if not base_name_for_image: base_name_for_image = name # Fallback
            self.image_blocks.append(get_profile_image_label(base_name_for_image))


    def init_ui(self):
        self.setStyleSheet(f"background-color: {DARK_BG_COLOR};")
        style = (
            f"QTextEdit {{ {TEXT_EDIT_STYLE_TRANSPARENT_BG} }}"
            f"QPushButton {{ {DEFAULT_BUTTON_STYLE} }}"
            f"QLabel {{ color: {WHITE_TEXT}; background-color: transparent; }}" # Ensure all labels are transparent by default
        )
        self.setStyleSheet(self.styleSheet() + style)

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(40)

        left = QVBoxLayout()
        hdr = QHBoxLayout()
        hdr.addStretch()
        self.label_section = QLabel("사건설명") # Will be updated
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
        # Use _get_image_path for background
        background_image_path = _get_image_path('background1.png').replace("\\", "/") # Ensure forward slashes for URL
        right_frame.setStyleSheet(
            f"background-image: url({background_image_path});"
            "background-repeat: no-repeat;"
            "background-position: center;"
            "background-size: cover;"
            "border-radius: 10px;" # Optional: round corners of background frame
        )
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(10, 10, 10, 10) # Padding inside the frame
        right_layout.setSpacing(0)

        self.image_label_container = QFrame() # Container to help with centering/scaling image
        self.image_label_container.setStyleSheet("background-color: transparent;")
        container_layout = QVBoxLayout(self.image_label_container)
        container_layout.setContentsMargins(0,0,0,0)
        
        self.image_label = QLabel() # This will hold the character/judge pixmap
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(True) # Let pixmap scale with label size
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setMinimumSize(200, 200) # Ensure it has some size
        container_layout.addWidget(self.image_label)

        right_layout.addWidget(self.image_label_container, 1) # Allow image to expand

        self.main_layout.addLayout(left, 3)
        self.main_layout.addWidget(right_frame, 2)

    def show_next_block(self):
        self.current_block_index += 1
        if self.current_block_index < len(self.display_blocks):
            self.text_display.setHtml(self.display_blocks[self.current_block_index])

            # Update section label
            if self.current_block_index == 0:
                self.label_section.setText("사건 개요")
            else:
                # Try to extract name from HTML block for section title
                html_content = self.display_blocks[self.current_block_index]
                match = re.search(r"<h3[^>]*>(.*?)<\/h3>", html_content, re.IGNORECASE)
                if match:
                    title_text = match.group(1)
                    # Further clean up if it contains "이름:"
                    name_match = re.search(r"이름\s*:\s*(\S+)\s*\((\S+)\)", title_text)
                    if name_match:
                        self.label_section.setText(f"{name_match.group(2)}: {name_match.group(1)}")
                    else:
                        self.label_section.setText(title_text[:15]) # Truncate if too long
                else:
                    self.label_section.setText(f"정보 #{self.current_block_index + 1}")


            img_widget_template = self.image_blocks[self.current_block_index] # This is a QLabel template
            if img_widget_template and img_widget_template.pixmap() and not img_widget_template.pixmap().isNull():
                # Scale pixmap to fit self.image_label while keeping aspect ratio
                scaled_pixmap = img_widget_template.pixmap().scaled(
                    self.image_label.size(), # Use current size of the label
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
            else:
                self.image_label.clear()
                self.image_label.setText(img_widget_template.text() if img_widget_template else "이미지 없음") # Show text if pixmap fails

            is_last = self.current_block_index == len(self.display_blocks) - 1
            self.next_button.setText("재판 시작" if is_last else "다음")
        else:
            if self.on_intro_finished:
                self.on_intro_finished()


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    # 더미 게임 컨트롤러 클래스
    class DummyGameController:
        pass
    
    # 더미 데이터 준비
    dummy_summary = """
    2024년 3월 15일 오후 2시경, 서울시 강남구 테헤란로의 한 카페에서 발생한 폭행 사건입니다.
    피해자 김영희(29세, 여성)는 카페에서 노트북으로 작업을 하던 중, 
    피고인 박민수(34세, 남성)로부터 갑작스러운 폭행을 당했다고 주장하고 있습니다.
    
    사건 당시 카페에는 여러 목격자들이 있었으며, CCTV 영상도 확보된 상태입니다.
    피고인 측은 정당방위를 주장하고 있어 진실 규명이 필요한 상황입니다.
    """
    
    dummy_profiles = [
        {
            "name": "박민수",
            "type": "defendant", 
            "gender": "male",
            "age": 34,
            "context": "사건의 피고인입니다.\n- 평소 성격이 급하다고 알려져 있음\n- 당일 스트레스를 많이 받고 있었다고 주장\n- 정당방위를 주장하고 있음"
        },
        {
            "name": "김영희",
            "type": "victim",
            "gender": "female", 
            "age": 29,
            "context": "사건의 피해자입니다.\n- 카페에서 평화롭게 작업을 하고 있었다고 주장\n- 갑작스러운 폭행을 당했다고 진술\n- 경미한 부상을 입음"
        },
        {
            "name": "이수진",
            "type": "witness",
            "gender": "female",
            "age": 25, 
            "context": "목격자입니다.\n- 사건 당시 카페에 있었음\n- 피고인이 먼저 시비를 걸었다고 증언\n- 명확한 상황을 기억하고 있다고 주장"
        },
        {
            "name": "정현우",
            "type": "witness", 
            "gender": "male",
            "age": 42,
            "context": "목격자입니다.\n- 카페 사장으로 전체 상황을 지켜봤음\n- CCTV 영상을 경찰에 제출함\n- 중립적인 입장에서 증언"
        }
    ]
    
    dummy_evidences = [
        {
            "id": 1,
            "name": "CCTV 영상",
            "type": "prosecutor",
            "description": "사건 당시 카페 내부 상황을 기록한 영상"
        },
        {
            "id": 2, 
            "name": "의료진단서",
            "type": "prosecutor",
            "description": "피해자의 부상 정도를 기록한 진단서"
        },
        {
            "id": 3,
            "name": "피고인 진술서", 
            "type": "attorney",
            "description": "피고인의 당시 상황에 대한 상세 진술"
        },
        {
            "id": 4,
            "name": "스트레스 관련 증명서",
            "type": "attorney", 
            "description": "피고인의 정신적 상태를 증명하는 서류"
        }
    ]
    
    def on_intro_finished():
        print("인트로 화면이 종료되었습니다!")
        QApplication.quit()
    
    # PyQt 애플리케이션 시작
    app = QApplication(sys.argv)
    
    # IntroScreen 생성
    intro_screen = IntroScreen(
        game_controller=DummyGameController(),
        on_intro_finished_callback=on_intro_finished,
        summary_text=dummy_summary,
        profiles_data=dummy_profiles,
        evidences_data=dummy_evidences
    )
    
    intro_screen.show()
    intro_screen.resize(1200, 800)
    intro_screen.setWindowTitle("IntroScreen 테스트")
    
    print("IntroScreen 테스트를 시작합니다...")
    print("- '다음' 버튼을 클릭하여 각 블록을 확인하세요")
    print("- 마지막에 '재판 시작' 버튼을 클릭하면 종료됩니다")
    
    sys.exit(app.exec_())