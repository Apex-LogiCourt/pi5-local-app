# base 이미지를 사용
FROM logicourt-base:latest

WORKDIR /app
# ✅ 명시적으로 core/requirements.txt 경로 지정
COPY core/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH="${PYTHONPATH}:/app"

COPY . .
CMD ["streamlit", "run", "core/chat.py"]
