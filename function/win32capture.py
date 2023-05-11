import ctypes
from ctypes.wintypes import DWORD, LONG, WORD

import cv2
import numpy as np


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", DWORD),
        ("biWidth", LONG),
        ("biHeight", LONG),
        ("biPlanes", WORD),
        ("biBitCount", WORD),
        ("biCompression", DWORD),
        ("biSizeImage", DWORD),
        ("biXPelsPerMeter", LONG),
        ("biYPelsPerMeter", LONG),
        ("biClrUsed", DWORD),
        ("biClrImportant", DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", DWORD * 3)]


Gdi32 = ctypes.windll.gdi32
User32 = ctypes.windll.user32


class ScreenCapture:
    def __init__(self, x, y, width, height, hwnd):
        self.x = x
        self.y = y
        self.hwnd = hwnd
        self.width = width
        self.height = height
        self.srcdc = User32.GetDC(hwnd)
        self.memdc = Gdi32.CreateCompatibleDC(self.srcdc)
        self.bmi = BITMAPINFO()
        self.bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        self.bmi.bmiHeader.biPlanes = 1
        self.bmi.bmiHeader.biBitCount = 32
        self.bmi.bmiHeader.biWidth = width
        self.bmi.bmiHeader.biHeight = -height
        self.bmp = Gdi32.CreateCompatibleBitmap(self.srcdc, width, height)
        Gdi32.SelectObject(self.memdc, self.bmp)
        self.bits = ctypes.create_string_buffer(self.width * self.height * 4)

    def cap(self):
        Gdi32.BitBlt(self.memdc, 0, 0, self.width, self.height, self.srcdc, self.x, self.y, 0x00CC0020)
        Gdi32.GetDIBits(self.memdc, self.bmp, 0, self.height, self.bits, self.bmi, 0)
        p = np.frombuffer(self.bits, dtype=np.uint8)
        p = p.reshape((self.height, self.width, 4))
        p = p[..., :3]  # drop alpha channel
        p = cv2.cvtColor(p, cv2.COLOR_BGR2RGB)  # convert to correct color format
        return p

    def __del__(self):
        Gdi32.DeleteObject(self.bmp)
        Gdi32.DeleteDC(self.memdc)
        User32.ReleaseDC(self.hwnd, self.srcdc)
