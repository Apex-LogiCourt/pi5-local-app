# 색상 상수
DARK_BG_COLOR = "#0f2748"
PRIMARY_BLUE = "#007bff"
SECONDARY_BLUE = "#2f5a68"
GOLD_ACCENT = "#f0c040"
WHITE_TEXT = "white"
LIGHT_GRAY_TEXT = "#ccc"
BLACK_COLOR = "black"
GREEN_BTN_COLOR = "#28a745"
DARK_GRAY_BTN_COLOR = "#3a3a3a"
MEDIUM_GRAY_BTN_COLOR = "#555"

# 공통 스타일
COMMON_PANEL_LABEL_STYLE = (
    f"color: {WHITE_TEXT}; font-size: 22px; font-weight: bold; "
    f"padding: 12px; border-radius: 12px;"
)
DEFAULT_BUTTON_STYLE = (
    f"background-color: {SECONDARY_BLUE}; color: {WHITE_TEXT}; "
    f"font-size: 18px; border-radius: 10px;"
)
TEXT_EDIT_STYLE_TRANSPARENT_BG = (
    f"background-color: transparent; color: {WHITE_TEXT}; "
    f"font-size: 15px; border: none;"
)
ROLE_TITLE_STYLE = (
    f"color: {GOLD_ACCENT}; font-size: 22px; font-weight: bold; "
    f"background-color: {BLACK_COLOR}; padding: 12px; border-radius: 8px;"
)
SIDE_BUTTON_STYLE = """
QPushButton {
    background-color: #2a4a70;
    color: white;
    font-size: 16px;
    border-radius: 6px;
    padding: 10px;
}
QPushButton:hover {
    font-size: 17px;
}
"""
TEXT_INPUT_STYLE = (
    f"background-color: {MEDIUM_GRAY_BTN_COLOR}; color: {WHITE_TEXT}; "
    f"font-size: 16px; border-radius: 6px;"
)
MIC_BUTTON_STYLE = "background-color: #2a4a70; border-radius: 40px;"

# HTML용 스타일
HTML_H3_STYLE = f"color: {WHITE_TEXT}; font-weight: bold;"
HTML_P_STYLE = f"color: {WHITE_TEXT}; margin: 5px 0;"
HTML_LI_STYLE = f"color: {WHITE_TEXT};"