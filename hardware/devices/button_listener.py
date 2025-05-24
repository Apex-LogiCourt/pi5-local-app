import RPi.GPIO as GPIO 
import time
import asyncio
import atexit
from hardware.api.http_request import handle_button_press

BUTTON_PIN_PROSECUTOR = 4
BUTTON_PIN_ATTORNEY = 14

def button_init():
    print("[GPIO] initializing")
    GPIO.setwarnings(False) 
    GPIO.setmode(GPIO.BCM) #BCM or BOARD

    GPIO.setup(BUTTON_PIN_PROSECUTOR, GPIO.IN, pull_up_down=GPIO.PUD_UP) 
    GPIO.add_event_detect(BUTTON_PIN_PROSECUTOR,GPIO.RISING)
    GPIO.add_event_callback(BUTTON_PIN_PROSECUTOR, button_callback_prosecutor)

    GPIO.setup(BUTTON_PIN_ATTORNEY, GPIO.IN, pull_up_down=GPIO.PUD_UP) 
    GPIO.add_event_detect(BUTTON_PIN_ATTORNEY,GPIO.RISING)
    GPIO.add_event_callback(BUTTON_PIN_ATTORNEY, button_callback_attorney)
    return

def button_callback_prosecutor(channel):
    print(f"Button pushed! {channel}")
    asyncio.get_event_loop().create_task(handle_button_press("prosecutor"))

def button_callback_attorney(channel):
    print(f"Button pushed! {channel}")
    asyncio.get_event_loop().create_task(handle_button_press("attorney"))

def cleanup_gpio():
    GPIO.cleanup()
    print("[GPIO] clean-up")

atexit.register(cleanup_gpio)


if __name__ == "__main__":
    button_init()
    for i in range(100):
        time.sleep(0.1)
    GPIO.cleanup()