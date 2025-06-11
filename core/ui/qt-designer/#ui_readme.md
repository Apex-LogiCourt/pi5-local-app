# PyQt Ui by QtDesigner

## 참고사항
리소스는 "pyrcc5 resources.qrc -o resource_rc.py" 명령으로 컴파일 가능합니다. (용량제한 업로드 불가)  
resource_rc를 임포트하면 간단하게 리소스 불러와서 사용할 수 있습니다.  
resource_rc.py와 *.ui가 같은 경로이면 되는 것 같네요.  
> :/images/...　　기본 UI 이미지 경로  
> :/assets/profile/...　　프로필 이미지 경로  
> :/fonts/...　　폰트 경로(normal, blod, exBlod, light) 일단 아무거나 넣음  
> 폰트는 혹시 몰라 넣어놨는데, pi에서 확인 필요할 듯 합니다.  

이미지의 경우, QLabel로 되어있습니다.  
기존과 동일하게 Pixmap으로 설정해야 합니다.  

디자이너에서 가능한 만큼 설정해놓았는데, 나머지는 코드로 작성해야 하네요...

## UI widget name
### [startWindow]
- (QDialog) startWindow : 메인 창
- (QPushButton) gameStartButton : 게임 시작 버튼
- (QPushButton) gameDescriptionButton : 게임 설명 버튼
- (QPushButton) gameTextModeButton : 텍스트모드 버튼

### [descriptionWindow]
- (QDialog) gameDescriptionWindow : 메인 창
- (QPushButton) backButton : 뒤로가기 버튼
- (QTextBrowser) descriptionText : 게임 설명 텍스트

### [generateWindow]
- (QDialog) generateWindow : 메인 창
- (QTextBrowser) overviewText : 사건 개요 텍스트
- (QTextBrowser) lawyerEvidenceText : 변호측 증거품 텍스트
- (QTextBrowser) prosecutorEvidenceText : 검사측 증거품 텍스트

### [generateWindow2]
- (QDialog) generateWindow2 : 메인 창  
- (QPushButton) nameLabel : 프로필 이름 텍스트 (버튼 상속 맞습니다. label이나 text들은 디자인이..^^;;)
- (QPushButton) overviewButton : 사건 개요 버튼
- (QPushButton) lawyerEvidenceButton : 변호측 증거품 버튼
- (QPushButton) prosecutorEvidenceButton : 검사측 증거품 버튼
- (QLabel) profileImage : 프로필 이미지
- (QLabel) profileLabel1 : 프로필1 텍스트
- (QLabel) profileLabel2 : 프로필2 텍스트
- (QLabel) profileLabel3 : 프로필3 텍스트
- (QLabel) profileLabel4 : 프로필4 텍스트

### [lawyerWindow]
- (QDialog) lawyerWindow : 메인 창
- (QPushButton) overviewButton : 사건 개요 버튼
- (QPushButton) evidenceButton : 증거품 버튼
- (QPushButton) textButton : 텍스트 입력 버튼
- (QPushButton) profileButton1 : 프로필 보기 버튼 1
- (QPushButton) profileButton2 : 프로필 보기 버튼 2
- (QPushButton) profileButton3 : 프로필 보기 버튼 3
- (QPushButton) profileButton4 : 프로필 보기 버튼 4
- (QPushButton) endButton : 변론종료 버튼
- (QPushButton) micButton : 마이크 녹음 버튼

### [prosecutorWindow] == lawyerWindow
- (QDialog) prosecutorWindow : 메인 창
- (QPushButton) overviewButton : 사건 개요 버튼
- (QPushButton) evidenceButton : 증거품 버튼
- (QPushButton) textButton : 텍스트 입력 버튼
- (QPushButton) profileButton1 : 프로필 보기 버튼 1
- (QPushButton) profileButton2 : 프로필 보기 버튼 2
- (QPushButton) profileButton3 : 프로필 보기 버튼 3
- (QPushButton) profileButton4 : 프로필 보기 버튼 4
- (QPushButton) endButton : 주장종료 버튼
- (QPushButton) micButton : 마이크 녹음 버튼

### [interrogationWindow]
- (QDialog) interrogationWindow : 메인 창
- (QPushButton) smallEvidenceLabel : 증거품 이미지(스캔 전) rfid 스캔 시 setVisible로 스왑必
- (QPushButton) largeEvidenceLabel : 증거품 이미지(스캔 후)
- (QLabel) profileImage : 프로필 이미지
- (QLabel) profileTextLabel : 프로필 텍스트
- (QLabel) textLabel : 하단 텍스트
- (QPushButton) textButton : 텍스트입력 버튼
- (QPushButton) micButton : 마이크 녹음 버튼
- (QPushButton) backButton : 뒤로가기 버튼

### [judgeWindow]
- (QDialog) judgeWindow : 메인 창
- (QTextBrowser) judgeText : 판결문 텍스트
- (QPushButton) backButton : 뒤로가기 버튼