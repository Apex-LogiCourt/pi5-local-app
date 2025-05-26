import asyncio
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from api.http_request import handle_nfc

"""
SDA : 24
SCK : 23
MOSI: 19
MISO: 21
GND : 6
RST : 22
3.3V: 1
"""

READER = SimpleMFRC522()
CARD_LIST = {0x00: "1", 0x01: "2", 0x03: "3", 0x04: "4"} #카드 스캔값 확인 후 수정해야함

SCAN_STATE = True

def get_card_num(card_id):
    return CARD_LIST.get(card_id, -1)

async def scan_rfid_loop():
    print("[RFID] 스캐너 시작")
    while SCAN_STATE:
        try:
            card_id, _ = READER.read()
            card_num = get_card_num(card_id)
            if card_num == -1:
                continue
            print(f"[RFID] Card No.{card_num} scanned")
            asyncio.get_event_loop().create_task(handle_nfc(card_num))

        except Exception as e:
            # print(f"[RFID] 오류 발생: {e}")
            pass

        await asyncio.sleep(0.5)
    GPIO.cleanup()

def rfid_exit():
    GPIO.cleanup()
    print("[RFID] cleanup complete.")