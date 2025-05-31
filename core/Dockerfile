# base 이미지를 사용
FROM logicourt-base:latest

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ENV PYTHONPATH=/app/core

COPY . .
CMD ["python", "controller.py"]
