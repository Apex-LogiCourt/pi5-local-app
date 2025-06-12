import sys
import os
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5 import uic
from typing import List
from data_models import Evidence 

class EvidenceWindow(QDialog):
    """생성자에 evidence 리스트랑 부모 윈도우 받기"""
    def __init__(self, evidences: List, parent=None):
        super(EvidenceWindow, self).__init__(parent)
        
        # UI 파일 로드
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'evidenceWindow.ui')
        uic.loadUi(ui_path, self)

        self.setWindowTitle("증거품 창")
        self._display_evidences(evidences)
        
    def _display_evidences(self, evidences: List):
        """증거품 리스트를 UI에 표시"""
        evidence_labels = [
            self.evidenceLabel1,
            self.evidenceLabel2, 
            self.evidenceLabel3,
            self.evidenceLabel4
        ]
        
        # 모든 라벨 초기화
        for label in evidence_labels:
            label.setText("")
            label.hide()
        
        # 증거품 데이터로 라벨 설정 (최대 4개)
        for i, evidence in enumerate(evidences[:4]):
            if i < len(evidence_labels):
                # Evidence 객체라면 name 속성 사용, dict라면 'name' 키 사용
                if hasattr(evidence, 'name'):
                    text = evidence.name
                elif isinstance(evidence, dict):
                    text = evidence.get('name', f'증거품 {i+1}')
                else:
                    text = str(evidence)
                    
                evidence_labels[i].setText(text)
                evidence_labels[i].show()

# 테스트용 메인 함수
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 테스트용 증거품 데이터
    test_evidences = [
        {"name": "피해자의 지갑"},
        {"name": "범인의 지문이 발견된 칼"},
        {"name": "CCTV 녹화 영상"},
        {"name": "목격자 진술서"}
    ]
    
    window = EvidenceWindow(test_evidences)
    window.show()
    
    sys.exit(app.exec_())
