# base 이미지를 사용
FROM logicourt-base:latest

# PyQt5 빌드 및 실행에 필요한 시스템 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Qt5 개발 도구 (PyQt5 빌드용)
    qt5-qmake \
    qtbase5-dev \
    qtbase5-dev-tools \
    pyqt5-dev-tools \
    # X11 관련
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxrandr2 \
    libxinerama1 \
    libxi6 \
    libxcursor1 \
    libxtst6 \
    libglib2.0-0 \
    libdbus-1-3 \
    # Qt5 런타임 라이브러리
    libqt5core5a \
    libqt5gui5 \
    libqt5widgets5 \
    libqt5network5 \
    # 폰트
    fonts-dejavu-core \
    fontconfig \
    # 오디오 (TTS용)
    libpulse0 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# Qt 리소스 파일 컴파일 (없을 때만)
RUN if [ ! -f ui/qt_designer/resource_rc.py ]; then \
        cd ui/qt_designer/assets && \
        pyrcc5 resource.qrc -o resource_rc.py && \
        mv resource_rc.py ../; \
    else \
        echo "resource_rc.py already exists, skipping compilation"; \
    fi

# 나눔고딕 폰트 설치
RUN mkdir -p /usr/share/fonts/truetype/nanum && \
    cp ui/qt_designer/assets/NanumGothic*.ttf /usr/share/fonts/truetype/nanum/ && \
    fc-cache -f -v

# PyQt5 GUI 실행
CMD ["python", "main.py"]
