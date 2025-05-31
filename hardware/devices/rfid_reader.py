import asyncio
import devices.lib.MFRC522 as MFRC522
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
    "050CE0D7": "1",
    "05167FD1": "2",
    "00E5C6F7": "3",
    "00E8564E": "4"
} #실물 카드에 번호 표시

SCAN_STATE = True

def uidToString(uid):
    mystring = ""
    for i in uid:
        mystring = format(i, '02X') + mystring
    return mystring

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
                    card_uid = uidToString(uid)
                    card_num = CARD_LIST.get(card_uid)
                    print(f"[RFID] Card No.{card_num} scanned")
                    asyncio.create_task(handle_nfc(card_num))
                else:
                    print("[RFID] Authentication error.")
        except Exception as e:
            print(f"[RFID] scanner error: {e}")
        await asyncio.sleep(0.5)

def rfid_exit():
    global SCAN_STATE
    SCAN_STATE = False
    print("[RFID] cleanup complete.")
    pass
