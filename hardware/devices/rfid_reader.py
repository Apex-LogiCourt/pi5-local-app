import asyncio
import lib.MFRC522 as MFRC522
import signal
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

READER = MFRC522.MFRC522()

CARD_LIST = {
    927176852798: "1",
    899780314557: "2",
    1064193818836: "3",
    336465494256: "4"
} # 실물 카드에 번호 표기

SCAN_STATE = True

def get_card_num(card_id):
    return CARD_LIST.get(card_id, -1)

async def scan_rfid_loop():
    print("[RFID] scanner starting ...")
    while SCAN_STATE:
        try:
            (status, TagType) = READER.MFRC522_Request(READER.PICC_REQIDL)
            if status == READER.MI_OK:
                (status, uid) = READER.MFRC522_SelectTagSN()
                if status == READER.MI_OK:
                    print(f"[RFID/scanner] {uid} detected.")
                    # print(f"[RFID] Card No.{card_num} scanned")
                    # asyncio.create_task(handle_nfc(card_num))
                else:
                    print("[RFID] Authentication error.")
        except Exception as e:
            print(f"[RFID] scanner error: {e}")
        await asyncio.sleep(0.5)

def rfid_exit():
    print("[RFID] cleanup complete.")
    pass