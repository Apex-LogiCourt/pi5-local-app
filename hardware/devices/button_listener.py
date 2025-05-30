import RPi.GPIO as GPIO 
import time
import asyncio
import atexit
from api.http_request import handle_button_press

BUTTON_PIN_PROSECUTOR = 4   # 좌상단부터 4, 5번째에 연결(GPIO 4, GND)
BUTTON_PIN_ATTORNEY = 14    # 우상단부터 3, 4번째에 연결(GND, GPIO 14)

last_pressed = {
    "prosecutor": 0,
    "attorney": 0
}
DEBOUNCE_TIME = 0.5

def button_init():
    print("[GPIO/BUTTON] initializing ...")
    GPIO.setwarnings(False) 
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(BUTTON_PIN_PROSECUTOR, GPIO.IN, pull_up_down=GPIO.PUD_UP) 
    GPIO.add_event_detect(BUTTON_PIN_PROSECUTOR, GPIO.RISING, callback=button_callback_prosecutor, bouncetime=50)

    GPIO.setup(BUTTON_PIN_ATTORNEY, GPIO.IN, pull_up_down=GPIO.PUD_UP) 
    GPIO.add_event_detect(BUTTON_PIN_ATTORNEY, GPIO.RISING, callback=button_callback_attorney, bouncetime=50)

def button_callback_prosecutor(channel):
    now = time.time()
    if now - last_pressed["prosecutor"] > DEBOUNCE_TIME:
        last_pressed["prosecutor"] = now
        print(f"[BUTTON] Button pushed!, PROSECUTOR")
        asyncio.create_task(handle_button_press("prosecutor"))
    else:
        # print("[prosecutor] Ignored due to debounce.")
        pass

def button_callback_attorney(channel):
    now = time.time()
    if now - last_pressed["attorney"] > DEBOUNCE_TIME:
        last_pressed["attorney"] = now
        print(f"[BUTTON] Button pushed!, ATTORNEY")
        asyncio.create_task(handle_button_press("attorney"))
    else:
        # print("[attorney] Ignored due to debounce.")
        pass

def button_exit():
    GPIO.cleanup()
    print("[GPIO/BUTTON] cleanup complete.")

atexit.register(button_exit)


# test
if __name__ == "__main__":
    button_init()
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        GPIO.cleanup()
