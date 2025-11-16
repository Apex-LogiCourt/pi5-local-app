import sys
import os
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5.QtGui import QPixmap
from PyQt5 import uic
from typing import List
from data_models import Evidence 

class EvidenceWindow(QDialog):
    """생성자에 evidence 리스트랑 부모 윈도우 받기"""
    def __init__(self, evidences: List[Evidence], parent=None):
        super(EvidenceWindow, self).__init__(parent)
        
        # UI 파일 로드
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'evidenceWindow.ui')
        uic.loadUi(ui_path, self)

        
        self.setWindowTitle("증거품 창")
        self._display_evidences(evidences)
        
    def _display_evidences(self, evidences: List[Evidence]):
        """증거품 리스트를 UI에 표시"""
        evidence_labels = [
            self.evidenceLabel1,
            self.evidenceLabel2, 
            self.evidenceLabel3,
            self.evidenceLabel4
        ]
        
        evidence_descriptions = [
            self.evidenceDescription1,
            self.evidenceDescription2,
            self.evidenceDescription3,
            self.evidenceDescription4
        ]

        evidence_images = [
            self.evidenceImage1,
            self.evidenceImage2,
            self.evidenceImage3,
            self.evidenceImage4
        ]

        default_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')

        for i, evidence in enumerate(evidences):
            evidence_labels[i].setText(evidence.name)
            evidence_descriptions[i].setText("\n".join(evidence.description))

            image_path = default_path + "/" + str(evidence.picture)
            if not(os.path.exists(image_path)):
                image_path = default_path + "/data/evidence_resource/deafult_image.png"
            evidence_images[i].setPixmap(QPixmap(f"{image_path}").scaled(100, 100))
            
        
# 테스트용 메인 함수
if __name__ == "__main__":
    import asyncio
    
    async def main():
        app = QApplication(sys.argv)
        
        from game_controller import GameController  # 게임 컨트롤러 임포트
        
        gc = GameController.get_instance()  # 게임 컨트롤러 인스턴스
        
        await gc.initialize()  # 게임 컨트롤러 초기화 (비동기)
        await gc.start_game()  # 게임 시작 (비동기)
        
        evidences = gc._case_data.evidences  # 게임 컨트롤러에서 증거 리스트 가져오기
        
        window = EvidenceWindow(evidences)
        window.show()
        
        sys.exit(app.exec_())
    
    # 비동기 함수 실행
    asyncio.run(main())
