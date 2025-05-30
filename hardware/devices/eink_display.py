import subprocess
import serial
import time
import numpy as np
import os

from PIL import Image, ImageDraw, ImageFont
from enum import Enum

from typing import List, Literal        #pi 테스트용
from dataclasses import dataclass       #pi 테스트용
# from core.data_models import Evidence #나중에 사용
@dataclass
class Evidence:
    name: str  # 증거품 이름(명사형) 
    type: Literal["attorney", "prosecutor"]  # 제출 주체 
    description: List[str]  # 증거 설명 (추가 가능)
    picture: str  # 사진 경로 (향후 구현)

RFCOMM_DEV = "/dev/rfcomm0" # Interface for Serial mapping of Bluetooth.

class EPD_MacAddress(Enum):
    EPD_01 = "EC:C9:FF:42:BA:C6"
    EPD_02 = ""
    EPD_03 = ""
    EPD_04 = ""

# EPD모듈 번호(1~4), 증거품 입력 시, 이미지 생성 후 해당 모듈에 전송
def update_and_sand_image(epd_index, evidence: Evidence):
    epd_mac = get_mac(epd_index)
    bind_rfcomm(epd_mac)

    img_path = make_epd_image(evidence)

    byte_data = convert_image_to_bytes(img_path)
    print(f"총 전송 크기: {len(byte_data)} bytes")
    send_bytes_over_serial(byte_data)
    return


def bind_rfcomm(mac_addr): #바인딩 이후, RFCOMM_DEV를 USBSerial처럼 사용
    if not os.path.exists(RFCOMM_DEV):
        print(f"{RFCOMM_DEV} 바인딩 시도...")
        try:
            subprocess.run(["sudo", "rfcomm", "bind", "0", mac_addr, "1"], check=True)
            print("rfcomm 바인딩 완료")
        except subprocess.CalledProcessError as e:
            print("rfcomm 바인딩 실패:", e)
    else:
        print(f"{RFCOMM_DEV} 이미 바인딩되어 있음")
    time.sleep(0.5) # 바인딩 안정화용 지연

def convert_image_to_bytes(image_path):
    img = Image.open(image_path).convert("1")
    arr = np.array(img).flatten()
    packed = np.packbits(arr ^ 1)  # 1=흰색, 0=검정 -> 반전 필요
    return packed

def send_bytes_over_serial(byte_data):
    try:
        with serial.Serial(RFCOMM_DEV, baudrate=115200, timeout=1) as ser:
            print("시리얼 포트 열림, 데이터 전송 중...")
            for i in range(0, len(byte_data), 512):
                chunk = byte_data[i:i+512].tobytes()
                ser.write(chunk)
                ser.flush()
                time.sleep(0.15)  # 안정성 확보용 지연
            ser.flush()
            time.sleep(0.2)
            ser.close()
            print("전송 완료")
    except serial.SerialException as e:
        print("시리얼 포트 오류:", e)

def get_evidence_image_path(e: Evidence):
    return e.picture

def get_mac(index):
    mac_list = list(EPD_MacAddress)
    return mac_list[index-1].value


#========== EPD용 이미지 생성 ==========
font_path = "/home/user/Desktop/fonts/NanumGothic.ttf" #pi 테스트용

def make_epd_image(evidence: Evidence, font_size=20, line_spacing=6):
    image_path = evidence.picture
    text = evidence.description[0]
    save_path = evidence.name + ".bmp"
    
    canvas = Image.new("1", (400, 300), 1) # 400*300의 캔버스 생성

    # 캔버스 좌상단에 증거품 이미지 삽입
    img = Image.open(image_path).convert("1")
    img = img.resize((150, 150))
    canvas.paste(img, (0, 0)) 

    # 텍스트 처리 시작
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(font_path, font_size)
    x, y = (150 + 15), (0 + 15)  #시작 위치
    max_width = 250
    max_height = 150

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
    print(f"기본 이미지 생성 완료: {save_path}")

    if len(evidence.description) > 1:
        update_epd_image(save_path, evidence)

        print("이미지 설명 추가 완료")

    return (save_path)


def update_epd_image(image_path, evidence: Evidence, font_size=20, line_spacing=6):
    # 기존 이미지 로드
    img = Image.open(image_path).convert("1")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, font_size)

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
    print(f"저장 완료: {image_path}")
    return 


# 테스트용. C 배열 스타일로 출력
def image_to_c_array(img_path, array_name="gImage_data"):
    img = Image.open(img_path).convert("1")
    if img.mode != "1":
        raise ValueError("이미지는 흑백 모드(1)여야 합니다.")
    data = np.array(img)
    flattened = data.flatten()
    packed = np.packbits(flattened ^ 1)  # 0=검정, 1=흰색

    print(f"const unsigned char {array_name}[{len(packed)}] = {{")
    for i in range(0, len(packed), 20):
        line = ", ".join(f"0x{b:02X}" for b in packed[i:i+20])
        print("  " + line + ",")
    print("};")
    return



##### TEST CODE #####
if __name__ == "__main__":
    i = 1
    e = Evidence(
        name="t-evidence",
        type='attorney',
        description=["증거품의 기본 설명입니다. 대충 어쩌구 저쩌구 적당한 설명.", "증거품의 추가 설명일까요? 테스트용 문장입니다.", "증거품의 두 번째 추가 설명입니다. 제발 버그 없이 작동하게 해주세요."],
        picture="/home/user/Desktop/evidence_image.jpg"
    )
    update_and_sand_image(i, e)
