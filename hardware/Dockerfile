# Python 3.11 베이스 이미지 사용
FROM --platform=linux/arm64 logicourt-base:latest

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 종속성 설치
RUN apt-get update && apt-get install -y \
    # 오디오 처리를 위한 라이브러리
    portaudio19-dev \
    alsa-utils \
    libasound2-dev \
    # 시리얼 통신 및 하드웨어 제어
    udev \
    # 이미지 처리
    libopenjp2-7-dev \
    libtiff5-dev \
    # 기타 빌드 도구
    gcc \
    g++ \
    make \
    # 정리
    && rm -rf /var/lib/apt/lists/*

# requirements.txt 먼저 복사하여 캐시 활용
COPY requirements.txt .

# Python 종속성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 포트 8300 노출
EXPOSE 8300

# 오디오 및 하드웨어 장치 접근을 위한 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV PULSE_SERVER=unix:/run/user/1000/pulse/native

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8300/docs || exit 1

# 애플리케이션 실행
CMD ["python", "main.py"]
