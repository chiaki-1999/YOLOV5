import ctypes
import logging
import os

import numpy

from util import milli_sleep

log = logging.getLogger(__name__)

root = os.path.abspath(os.path.dirname(__file__))
dll_file = os.path.join(root, 'mouse.dll')

with open(dll_file, 'rb') as f:
    try:
        driver = ctypes.windll.LoadLibrary(dll_file)
        ok = driver.device_open() == 1
    except OSError:
        log.exception("Failed to load DLL file: %s", dll_file)
        ok = False


class Mouse:
    class mouse:
        @staticmethod
        def press(code):
            if ok:
                driver.mouse_down(code)

        @staticmethod
        def release(code):
            if ok:
                driver.mouse_up(code)

        @staticmethod
        def click(code):
            if ok:
                driver.mouse_down(code)
                milli_sleep(numpy.random.uniform(0.015, 0.03))
                driver.mouse_up(code)
                milli_sleep(numpy.random.uniform(0.015, 0.03))

        @staticmethod
        def scroll(a):
            if ok:
                driver.scroll(a)

        @staticmethod
        def move(x, y):
            if ok and x != 0 and y != 0:
                driver.moveR(x, y)

    class keyboard:
        @staticmethod
        def press(code):
            if ok:
                driver.key_down(code)

        @staticmethod
        def release(code):
            if ok:
                driver.key_up(code)

        @staticmethod
        def click(code):
            if ok:
                driver.key_down(code)
                driver.key_up(code)
