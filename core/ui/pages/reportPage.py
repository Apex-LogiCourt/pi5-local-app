import sys
import os
from PyQt5.QtWidgets import QDialog, QWidget, QApplication, QGraphicsOpacityEffect
from PyQt5.QtGui import QPixmap, QFont, QFontMetrics
from PyQt5.QtCore import QRect, Qt
from PyQt5 import uic

class ReportPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # UI 파일 로드
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'reportPage.ui')
        uic.loadUi(ui_path, self)
        
        # 이미지 투명도 설정
        self.setup_image_opacity()
        
        # 테스트 이미지 로드 (예시)
        self.load_test_images()
        
        # 초기 위치 저장 (비율 계산용)
        self.save_initial_positions()
    
    def save_initial_positions(self):
        """초기 위치와 크기를 비율로 저장"""
        # panPros 기준으로 내부 위젯들의 상대 위치 저장
        self.base_panel_width = 680  # 초기 패널 너비 (대략)
        self.base_panel_height = 620  # 초기 패널 높이 (대략)
        panel_width = self.base_panel_width
        panel_height = self.base_panel_height
        
        # 초기 폰트 크기 저장
        self.base_fonts = {
            'header': 16,
            'label': 15,
            'spec': 13,
            'comment': 14,
            'total': 24,
        }
        
        # 각 위젯의 초기 위치를 비율로 저장
        self.initial_ratios = {
            'header': (20/panel_width, 20/panel_height, 200/panel_width, 22/panel_height),
            'debate_label': (20/panel_width, 58/panel_height, 200/panel_width, 21/panel_height),
            'debate_progress': (230/panel_width, 58/panel_height, 410/panel_width, 21/panel_height),
            'debate_spec': (20/panel_width, 85/panel_height, 640/panel_width, 40/panel_height),
            'exam_label': (20/panel_width, 135/panel_height, 250/panel_width, 21/panel_height),
            'exam_progress': (280/panel_width, 135/panel_height, 360/panel_width, 21/panel_height),
            'exam_spec': (20/panel_width, 162/panel_height, 640/panel_width, 40/panel_height),
            'rebuttal_label': (20/panel_width, 212/panel_height, 200/panel_width, 21/panel_height),
            'rebuttal_progress': (230/panel_width, 212/panel_height, 410/panel_width, 21/panel_height),
            'rebuttal_spec': (20/panel_width, 239/panel_height, 640/panel_width, 40/panel_height),
            'comment': (20/panel_width, 295/panel_height, 640/panel_width, 200/panel_height),
            'total_score': (20/panel_width, 520/panel_height, 150/panel_width, 30/panel_height),
            'image': (0, 0, 1.0, 1.0),  # 패널 전체 크기 (비율 100%)
        }
    
    def resizeEvent(self, event):
        """창 크기 변경 시 위젯들을 동적으로 재배치"""
        super().resizeEvent(event)
        
        # 각 패널의 현재 크기 가져오기
        pros_rect = self.panPros.geometry()
        att_rect = self.panAtt.geometry()
        
        # 검사 패널 내부 위젯 재배치
        self.resize_panel_widgets(
            pros_rect,
            self.lblProsHeader,
            self.lblDebateLabelPros,
            self.progressDebate,
            self.lblDebateSpecPros,
            self.lblExamLabelPros,
            self.progressExam,
            self.lblExamSpecPros,
            self.lblRebuttalLabelPros,
            self.progressRebuttal,
            self.lblRebuttalSpecPros,
            self.lblProsComment,
            self.lblProsTotalScore,
            self.imgProsecutor
        )
        
        # 변호인 패널 내부 위젯 재배치
        self.resize_panel_widgets(
            att_rect,
            self.lblAttHeader,
            self.lblDebateLabelAtt,
            self.progressDebate2,
            self.lblDebateSpecAtt,
            self.lblExamLabelAtt,
            self.progressExam2,
            self.lblExamSpecAtt,
            self.lblRebuttalLabelAtt,
            self.progressRebuttal2,
            self.lblRebuttalSpecAtt,
            self.lblAttComment,
            self.lblAttTotalScore,
            self.imgAttorney
        )
    
    def resize_panel_widgets(self, panel_rect, header, debate_lbl, debate_prog, debate_spec,
                            exam_lbl, exam_prog, exam_spec, rebuttal_lbl, rebuttal_prog,
                            rebuttal_spec, comment, total_score, image):
        """패널 내부 위젯들을 비율에 맞게 재배치"""
        pw = panel_rect.width()
        ph = panel_rect.height()
        
        # 기본 폰트 크기 조절 (패널 크기 기준)
        scale_factor = min(pw / self.base_panel_width, ph / self.base_panel_height)
        scale_factor = max(0.5, min(scale_factor, 1.0))  # 0.5배 ~ 1.0배로 제한
        
        ratios = self.initial_ratios
        
        # 각 위젯 재배치 (비율 기반)
        header_rect = QRect(
            int(pw * ratios['header'][0]),
            int(ph * ratios['header'][1]),
            int(pw * ratios['header'][2]),
            int(ph * ratios['header'][3])
        )
        header.setGeometry(header_rect)
        # 헤더 폰트 (레이블 크기에 맞춤)
        header_font = self.fit_font_to_label(header, "나눔고딕 ExtraBold", 
                                             self.base_fonts['header'] * scale_factor, bold=True)
        header.setFont(header_font)
        
        debate_lbl_rect = QRect(
            int(pw * ratios['debate_label'][0]),
            int(ph * ratios['debate_label'][1]),
            int(pw * ratios['debate_label'][2]),
            int(ph * ratios['debate_label'][3])
        )
        debate_lbl.setGeometry(debate_lbl_rect)
        debate_lbl_font = self.fit_font_to_label(debate_lbl, "나눔고딕 ExtraBold",
                                                  self.base_fonts['label'] * scale_factor, bold=True)
        debate_lbl.setFont(debate_lbl_font)
        
        debate_prog.setGeometry(QRect(
            int(pw * ratios['debate_progress'][0]),
            int(ph * ratios['debate_progress'][1]),
            int(pw * ratios['debate_progress'][2]),
            int(ph * ratios['debate_progress'][3])
        ))
        
        debate_spec_rect = QRect(
            int(pw * ratios['debate_spec'][0]),
            int(ph * ratios['debate_spec'][1]),
            int(pw * ratios['debate_spec'][2]),
            int(ph * ratios['debate_spec'][3])
        )
        debate_spec.setGeometry(debate_spec_rect)
        debate_spec_font = self.fit_font_to_label(debate_spec, "나눔고딕",
                                                   self.base_fonts['spec'] * scale_factor, bold=True)
        debate_spec.setFont(debate_spec_font)
        
        exam_lbl_rect = QRect(
            int(pw * ratios['exam_label'][0]),
            int(ph * ratios['exam_label'][1]),
            int(pw * ratios['exam_label'][2]),
            int(ph * ratios['exam_label'][3])
        )
        exam_lbl.setGeometry(exam_lbl_rect)
        exam_lbl_font = self.fit_font_to_label(exam_lbl, "나눔고딕 ExtraBold",
                                                self.base_fonts['label'] * scale_factor, bold=True)
        exam_lbl.setFont(exam_lbl_font)
        
        exam_prog.setGeometry(QRect(
            int(pw * ratios['exam_progress'][0]),
            int(ph * ratios['exam_progress'][1]),
            int(pw * ratios['exam_progress'][2]),
            int(ph * ratios['exam_progress'][3])
        ))
        
        exam_spec_rect = QRect(
            int(pw * ratios['exam_spec'][0]),
            int(ph * ratios['exam_spec'][1]),
            int(pw * ratios['exam_spec'][2]),
            int(ph * ratios['exam_spec'][3])
        )
        exam_spec.setGeometry(exam_spec_rect)
        exam_spec_font = self.fit_font_to_label(exam_spec, "나눔고딕",
                                                 self.base_fonts['spec'] * scale_factor, bold=True)
        exam_spec.setFont(exam_spec_font)
        
        rebuttal_lbl_rect = QRect(
            int(pw * ratios['rebuttal_label'][0]),
            int(ph * ratios['rebuttal_label'][1]),
            int(pw * ratios['rebuttal_label'][2]),
            int(ph * ratios['rebuttal_label'][3])
        )
        rebuttal_lbl.setGeometry(rebuttal_lbl_rect)
        rebuttal_lbl_font = self.fit_font_to_label(rebuttal_lbl, "나눔고딕 ExtraBold",
                                                    self.base_fonts['label'] * scale_factor, bold=True)
        rebuttal_lbl.setFont(rebuttal_lbl_font)
        
        rebuttal_prog.setGeometry(QRect(
            int(pw * ratios['rebuttal_progress'][0]),
            int(ph * ratios['rebuttal_progress'][1]),
            int(pw * ratios['rebuttal_progress'][2]),
            int(ph * ratios['rebuttal_progress'][3])
        ))
        
        rebuttal_spec_rect = QRect(
            int(pw * ratios['rebuttal_spec'][0]),
            int(ph * ratios['rebuttal_spec'][1]),
            int(pw * ratios['rebuttal_spec'][2]),
            int(ph * ratios['rebuttal_spec'][3])
        )
        rebuttal_spec.setGeometry(rebuttal_spec_rect)
        rebuttal_spec_font = self.fit_font_to_label(rebuttal_spec, "나눔고딕",
                                                     self.base_fonts['spec'] * scale_factor, bold=True)
        rebuttal_spec.setFont(rebuttal_spec_font)
        
        comment_rect = QRect(
            int(pw * ratios['comment'][0]),
            int(ph * ratios['comment'][1]),
            int(pw * ratios['comment'][2]),
            int(ph * ratios['comment'][3])
        )
        comment.setGeometry(comment_rect)
        comment_font = self.fit_font_to_label(comment, "나눔고딕",
                                               self.base_fonts['comment'] * scale_factor)
        comment.setFont(comment_font)
        
        total_score_rect = QRect(
            int(pw * ratios['total_score'][0]),
            int(ph * ratios['total_score'][1]),
            int(pw * ratios['total_score'][2]),
            int(ph * ratios['total_score'][3])
        )
        total_score.setGeometry(total_score_rect)
        total_score_font = self.fit_font_to_label(total_score, "나눔고딕 ExtraBold",
                                                   self.base_fonts['total'] * scale_factor, bold=True)
        total_score.setFont(total_score_font)
        
        image.setGeometry(QRect(
            int(pw * ratios['image'][0]),
            int(ph * ratios['image'][1]),
            int(pw * ratios['image'][2]),
            int(ph * ratios['image'][3])
        ))
    
    def fit_font_to_label(self, label, font_family, base_size, bold=False):
        """레이블 크기에 맞춰서 폰트 크기를 자동 조절"""
        text = label.text()
        if not text:
            font = QFont(font_family, int(base_size))
            if bold:
                font.setBold(True)
            return font
        
        # 레이블 크기
        label_width = label.width()
        label_height = label.height()
        
        # 시작 폰트 크기
        font_size = int(base_size)
        min_font_size = 8  # 최소 폰트 크기
        
        # 폰트 크기를 줄여가면서 레이블에 맞는지 확인
        for size in range(font_size, min_font_size - 1, -1):
            test_font = QFont(font_family, size)
            if bold:
                test_font.setBold(True)
            
            metrics = QFontMetrics(test_font)
            
            # wordWrap이 활성화된 경우
            if label.wordWrap():
                # boundingRect로 실제 텍스트 영역 계산
                flags = int(Qt.TextWordWrap) | int(label.alignment())
                rect = metrics.boundingRect(
                    0, 0, label_width, label_height,
                    flags,
                    text
                )
                if rect.width() <= label_width and rect.height() <= label_height:
                    return test_font
            else:
                # 한 줄인 경우
                text_width = metrics.horizontalAdvance(text)
                text_height = metrics.height()
                if text_width <= label_width and text_height <= label_height:
                    return test_font
        
        # 최소 폰트 크기 반환
        final_font = QFont(font_family, min_font_size)
        if bold:
            final_font.setBold(True)
        return final_font
    
    def setup_image_opacity(self):
        """이미지 레이블에 투명도 효과 적용"""
        # 검사 이미지 투명도
        prosecutor_opacity = QGraphicsOpacityEffect()
        prosecutor_opacity.setOpacity(0.5)  # 30% 불투명도
        self.imgProsecutor.setGraphicsEffect(prosecutor_opacity)
        
        # 변호인 이미지 투명도
        attorney_opacity = QGraphicsOpacityEffect()
        attorney_opacity.setOpacity(0.5)  # 30% 불투명도
        self.imgAttorney.setGraphicsEffect(attorney_opacity)
    
    def load_test_images(self):
        """테스트용 이미지 로드"""
        # 이미지 경로 (상대 경로)
        base_path = os.path.join(os.path.dirname(__file__), '..', 'assets')
        
        prosecutor_img = os.path.join(base_path, 'win_prosecutor.png')
        attorney_img = os.path.join(base_path, 'lose_attorney.png')
        
        # 파일이 존재하면 로드
        if os.path.exists(prosecutor_img):
            self.imgProsecutor.setPixmap(QPixmap(prosecutor_img))
        
        if os.path.exists(attorney_img):
            self.imgAttorney.setPixmap(QPixmap(attorney_img))
    
    def update_scores(self, prosecutor_data, attorney_data):
        """점수 데이터 업데이트 (나중에 사용)"""
        # 검사 쪽
        self.lblDebateLabelPros.setText(f"주장 (Debate) · {prosecutor_data.get('debate_score', 15)}점")
        self.progressDebate.setValue(prosecutor_data.get('debate_percent', 75))
        self.lblDebateSpecPros.setText(prosecutor_data.get('debate_detail', ''))
        
        self.lblExamLabelPros.setText(f"심문 (Examination) · {prosecutor_data.get('exam_score', 20)}점")
        self.progressExam.setValue(prosecutor_data.get('exam_percent', 65))
        self.lblExamSpecPros.setText(prosecutor_data.get('exam_detail', ''))
        
        self.lblRebuttalLabelPros.setText(f"반박 (Rebuttal) · {prosecutor_data.get('rebuttal_score', 10)}점")
        self.progressRebuttal.setValue(prosecutor_data.get('rebuttal_percent', 50))
        self.lblRebuttalSpecPros.setText(prosecutor_data.get('rebuttal_detail', ''))
        
        self.lblProsComment.setText(prosecutor_data.get('comment', ''))
        self.lblProsTotalScore.setText(f"총점 {prosecutor_data.get('total', 45)}점")
        
        # 변호인 쪽
        self.lblDebateLabelAtt.setText(f"주장 (Debate) · {attorney_data.get('debate_score', 15)}점")
        self.progressDebate2.setValue(attorney_data.get('debate_percent', 67))
        self.lblDebateSpecAtt.setText(attorney_data.get('debate_detail', ''))
        
        self.lblExamLabelAtt.setText(f"심문 (Examination) · {attorney_data.get('exam_score', 20)}점")
        self.progressExam2.setValue(attorney_data.get('exam_percent', 60))
        self.lblExamSpecAtt.setText(attorney_data.get('exam_detail', ''))
        
        self.lblRebuttalLabelAtt.setText(f"반박 (Rebuttal) · {attorney_data.get('rebuttal_score', 10)}점")
        self.progressRebuttal2.setValue(attorney_data.get('rebuttal_percent', 40))
        self.lblRebuttalSpecAtt.setText(attorney_data.get('rebuttal_detail', ''))
        
        self.lblAttComment.setText(attorney_data.get('comment', ''))
        self.lblAttTotalScore.setText(f"총점 {attorney_data.get('total', 40)}점")


# 테스트용 메인 함수
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 폰트 설정 (나눔고딕이 설치되어 있지 않으면 기본 폰트 사용)
    from PyQt5.QtGui import QFontDatabase, QFont
    font_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'NanumGothic.ttf')
    if os.path.exists(font_path):
        QFontDatabase.addApplicationFont(font_path)
        app.setFont(QFont("나눔고딕", 10))
    
    window = ReportPage()
    window.show()
    
    sys.exit(app.exec_())
