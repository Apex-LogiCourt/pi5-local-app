import sys
import core.ui.qt_designer.resource_rc as resource_rc # 리소스 불러오기

from PyQt5.QtWidgets import *
from PyQt5 import uic

#UI파일 연결
#단, UI파일은 Python 코드 파일과 같은 디렉토리에 위치해야한다.
startWindowUi = uic.loadUiType("core/ui/qt_designer/startWindow.ui")[0]
descriptionWindowUi = uic.loadUiType("core/ui/qt_designer/gameDescriptionWindow.ui")[0]


class startWindowClass(QDialog, startWindowUi) :
    def __init__(self) :
        super().__init__()
        self.setupUi(self)

        # 설명창 인스턴스 생성
        self.descriptionWindow = descriptionWindowClass()

        # 버튼 이벤트 연결
        self.gameDescriptionButton.clicked.connect(self.descriptionClick)
    
    # 버튼 이벤트 함수
    def startClick(self):
        pass
    def descriptionClick(self):
        self.hide()
        self.descriptionWindow.show()
    def textClick(self):
        pass

class descriptionWindowClass(QDialog, descriptionWindowUi) :
    def __init__(self) :
        super().__init__()
        self.setupUi(self)

        self.backButton.clicked.connect(self.backClick)
    
    def backClick(self):
        self.hide()
        startWindow.show()
        pass

if __name__ == "__main__" :
    #QApplication : 프로그램을 실행시켜주는 클래스
    app = QApplication(sys.argv) 

    #startWindowClass의 인스턴스 생성
    startWindow = startWindowClass()

    #프로그램 화면을 보여주는 코드
    startWindow.show()

    #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()