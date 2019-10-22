import time

from pynput.keyboard import Key, Controller

keyboard = Controller()

time.sleep(3)

keyboard.press(Key.space)
keyboard.release(Key.space)

time.sleep(1)

keyboard.press(Key.space)
keyboard.release(Key.space)