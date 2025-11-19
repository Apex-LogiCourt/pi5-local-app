import subprocess
import serial
import time
import numpy as np
import os
import traceback

from PIL import Image, ImageDraw, ImageFont, ImageOps
from typing import List
from data_models import Evidence

RFCOMM_DEV = "/dev/rfcomm" # Interface for Serial mapping of Bluetooth.

EPD_MacAddress = {
    1: "EC:C9:FF:42:BA:C6",
    2: "EC:C9:FF:42:C1:B2",
    3: "EC:C9:FF:42:C1:CA",
    4: "C0:5D:89:C4:F2:7A"
}

# EPD모듈 번호(1~4), 증거품 입력 시, 이미지 생성 후 해당 모듈에 전송
def update_and_sand_image(epd_index: int, evidence: Evidence):
    try:
        epd_mac = EPD_MacAddress[epd_index]
        rfcomm = bind_rfcomm(epd_index, epd_mac)
        img_path = make_epd_image(evidence)
        inversion_image(img_path)
        byte_data = convert_image_to_bytes(img_path)
        send_bytes_over_serial(rfcomm, byte_data)
    except Exception as e:
        print(f"[HW/EPD] epd update error: {e}")
        traceback.print_exc()
    return


def bind_rfcomm(epd_index, mac_addr): #바인딩 이후, RFCOMM_DEV를 USBSerial처럼 사용
    epd_rfcomm = f"{RFCOMM_DEV}{epd_index - 1}"
    if not os.path.exists(epd_rfcomm):
        print(f"[HW/EPD]{epd_rfcomm} 바인딩 시도...")
        try:
            subprocess.run(["sudo", "rfcomm", "bind", str(epd_index-1), mac_addr, "1"], check=True)
            print("[HW/EPD]rfcomm 바인딩 완료")
        except subprocess.CalledProcessError as e:
            print("[HW/EPD]rfcomm 바인딩 실패:", e)
    else:
        pass
    time.sleep(0.5) # 바인딩 안정화용 지연
    return epd_rfcomm

def convert_image_to_bytes(image_path):
    img = Image.open(image_path).convert("1")
    arr = np.array(img).flatten()
    packed = np.packbits(arr)
    return packed

def send_bytes_over_serial(rfcomm, byte_data):
    try:
        with serial.Serial(rfcomm, baudrate=115200, timeout=1) as ser:
            print("[HW/EPD]시리얼 포트 열림, 데이터 전송 중...")
            for i in range(0, len(byte_data), 512):
                chunk = byte_data[i:i+512].tobytes()
                ser.write(chunk)
                ser.flush()
                time.sleep(0.15)  # 안정성 확보용 지연
            ser.flush()
            time.sleep(0.2)
            ser.close()
            print(f"[HW/EPD] {rfcomm}전송 완료")
    except serial.SerialException as e:
        print("[HW/EPD]시리얼 포트 오류:", e)

#========== EPD용 이미지 생성 ==========
FONT_PATH = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf" #실제 폰트경로
TITLE_FONT_PATH = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf" #실제 폰트경로

def make_epd_image(evidence: Evidence, font_size=20, line_spacing=6):
    #image_path = "/home/user/Desktop/swfesta/pi5-local-app/" + evidence.picture
    image_path = evidence.picture
    text = evidence.description[0]
    #save_path = evidence.name + ".bmp"
    save_path = "/home/user/Desktop/swfesta/pi5-local-app/data/evidence_resource" + evidence.name + ".bmp"
    
    # 400*300의 캔버스 생성
    canvas = Image.new("1", (400, 300), 1)
    draw = ImageDraw.Draw(canvas)

    # 💬 상단 이름 텍스트 출력
    title_font_size = 20  # or customize
    title_font = ImageFont.truetype(TITLE_FONT_PATH, title_font_size)
    title_text = evidence.name
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_height = title_bbox[3] - title_bbox[1]
    title_x = (400 - title_width) // 2
    title_y = (30 - title_height) // 2  # 위 padding 5, 아래 padding 5 고려
    draw.text((title_x, title_y), title_text, font=title_font, fill=0)

    # 캔버스 좌상단에 증거품 이미지 삽입
    img = Image.open(image_path).convert("1")
    img = img.resize((150, 150))
    canvas.paste(img, (0, 30)) 

    # 텍스트 처리 시작
    font = ImageFont.truetype(FONT_PATH, font_size)
    x, y = (150 + 15), (30 + 15)  #시작 위치
    max_width = 250 - 10
    max_height = 150 - 5

    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split(" ")
        line = ""
        for word in words:
            test_line = line + word + " "
            bbox = draw.textbbox((0, 0), test_line, font=font)
            w = bbox[2] - bbox[0] #텍스트 폭 측정
            if w > max_width: #안들어가면 줄바꿈
                lines.append(line)
                line = word + " "
            else:
                line = test_line
        lines.append(line)

    for line in lines:
        if y + font_size > max_height:
            break
        draw.text((x, y), line.strip(), font=font, fill=0)
        y += font_size + line_spacing #줄간격 설정

    canvas.save(save_path)
    print(f"[HW/EPD]기본 이미지 생성 완료: {save_path}")

    if len(evidence.description) > 1:
        update_epd_image(save_path, evidence)
        print("[HW/EPD]이미지 설명 추가 완료")
    return (save_path)


def update_epd_image(image_path, evidence: Evidence, font_size=20, line_spacing=6):
    # 기존 이미지 로드
    img = Image.open(image_path).convert("1")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, font_size)

    # 추가 설명문 제작
    text = "".join(word + "\n" for word in evidence.description[1:])

    # 텍스트 출력 시작 위치 (하단 절반 영역)
    x, y = (0 + 15), (150 + 10)
    max_width = 400 - 10
    max_height = 300

    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split(" ")
        line = ""
        for word in words:
            test_line = line + word + " "
            bbox = draw.textbbox((0, 0), test_line, font=font)
            w = bbox[2] - bbox[0]
            if w > max_width:
                lines.append(line)
                line = word + " "
            else:
                line = test_line
        lines.append(line)

    for line in lines:
        if y + font_size > max_height:
            break
        draw.text((x, y), line.strip(), font=font, fill=0)
        y += font_size + line_spacing

    img.save(image_path)
    print(f"[HW/EPD]이미지 설명 추가 완료: {image_path}")
    return

def inversion_image(image_path):
    try:
        img = Image.open(image_path).convert("1")

        img = ImageOps.mirror(img)
        # img_l = img.convert("L")
        # img_inverted = ImageOps.invert(img_l)

        # img_final = img_inverted.convert("1")
        # img_final.save(image_path)
        img.save(image_path)
    except Exception as e:
        print(f"[HW/EPD] 이미지 반전 오류: {e}")
    return image_path

##### TEST CODE #####
if __name__ == "__main__":
    e = Evidence(
        id=4,
        name="t-evidence",
        type='attorney',
        description=["증거품의 기본 설명입니다. 대충 어쩌구 저쩌구 적당한 설명.", "증거품의 추가 설명일까요? 테스트용 문장입니다.", "증거품의 두 번째 추가 설명입니다. 제발 버그 없이 작동하게 해주세요."],
        picture="/home/user/Desktop/evidence_image.jpg"
    )
    update_and_sand_image(e.id, e)
