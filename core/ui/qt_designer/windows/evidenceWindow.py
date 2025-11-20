import sys
import os
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5.QtGui import QPixmap
from PyQt5 import uic
from typing import List
from data_models import Evidence 

class EvidenceWindow(QDialog):
    """생성자에 evidence 리스트랑 부모 윈도우 받기"""
    def __init__(self, evidences: List = None, parent=None):
        super(EvidenceWindow, self).__init__(parent)

        # UI 파일 로드
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'evidenceWindow.ui')
        uic.loadUi(ui_path, self)

        
        self.setWindowTitle("증거품 창")
        self.evidences = evidences if evidences is not None else []
        self._display_evidences(self.evidences)

    def _display_evidences(self, evidences: List):
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

        loading_image_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'loading.png')

        # 증거품이 없으면 "생성 중" 표시
        if not evidences or len(evidences) == 0:
            for i in range(4):
                evidence_labels[i].setText("증거품 생성 중...")
                evidence_descriptions[i].setText("증거품을 생성하고 있습니다.\n잠시만 기다려주세요.")
                # loading.png를 기본 이미지로 표시
                if os.path.exists(loading_image_path):
                    evidence_images[i].setPixmap(QPixmap(loading_image_path).scaled(90, 90))
                else:
                    evidence_images[i].clear()
            return

        # 증거품이 있으면 표시
        for i, evidence in enumerate(evidences):
            if i < len(evidence_labels):
                evidence_labels[i].setText(evidence.name)
                evidence_descriptions[i].setText("\n".join(evidence.description))

                # 이미지 표시 (이미지가 없거나 None이면 loading.png 사용)
                if evidence.picture:
                    image_path = str(evidence.picture)
                    if os.path.exists(image_path):
                        evidence_images[i].setPixmap(QPixmap(image_path).scaled(90, 90))
                    else:
                        # 이미지 파일이 없으면 loading.png 사용
                        if os.path.exists(loading_image_path):
                            evidence_images[i].setPixmap(QPixmap(loading_image_path).scaled(90, 90))
                        else:
                            evidence_images[i].clear()
                else:
                    # picture가 None이면 loading.png 사용 (이미지 생성 중)
                    if os.path.exists(loading_image_path):
                        evidence_images[i].setPixmap(QPixmap(loading_image_path).scaled(90, 90))
                    else:
                        evidence_images[i].clear()

    def update_evidences(self, evidences: List):
        """증거품 리스트 업데이트 (증거품 생성 완료 후 호출)"""
        self.evidences = evidences
        self._display_evidences(evidences)
        
# 테스트용 메인 함수
if __name__ == "__main__":
    import asyncio
    
    async def main():
        app = QApplication(sys.argv)
        
        from game_controller import GameController  # 게임 컨트롤러 임포트
        
        gc = GameController.get_instance()  # 게임 컨트롤러 인스턴스
        
        await gc.initialize()  # 게임 컨트롤러 초기화 (비동기)
        await gc.prepare_case_data()  # 게임 시작 (비동기)
        
        evidences = gc._case_data.evidences  # 게임 컨트롤러에서 증거 리스트 가져오기
        
        window = EvidenceWindow(evidences)
        window.show()
        
        sys.exit(app.exec_())
    
    # 비동기 함수 실행
    asyncio.run(main())
