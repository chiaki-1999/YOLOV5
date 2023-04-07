import numpy as np
import win32gui
import win32ui
import win32gui
import win32ui


class GrabScreen:
    def __init__(self):
        self.hwnd = None
        self.w = None
        self.h = None
        self.hdc = None
        self.mdc = None
        self.bitmap = None

    def init(self, w, h):
        self.w = w
        self.h = h
        self.hwnd = win32gui.GetDesktopWindow()
        self.hdc = win32gui.GetWindowDC(self.hwnd)
        self.mdc = win32ui.CreateDCFromHandle(self.hdc)
        self.bitmap = win32ui.CreateBitmap()
        self.bitmap.CreateCompatibleBitmap(self.mdc, self.w, self.h)

    def capture(self, x, y):
        self.mdc.SelectObject(self.mbitmap)
        self.mdc.BitBlt((0, 0), (self.w, self.h), self.hdc, (x, y), win32con.SRCCOPY)
        signed_ints_array = self.mbitmap.GetBitmapBits(True)
        img = np.frombuffer(signed_ints_array, dtype='uint8')
        img.shape = (self.h, self.w, 4)
        img = img[..., :3]
        img = np.ascontiguousarray(img)
        return img

    def release_resource(self):
        if self.mdc:
            self.mdc.DeleteDC()
            self.mdc = None
        if self.bitmap:
            win32gui.DeleteObject(self.mbitmap.GetHandle())
            self.bitmap = None
        if self.hdc:
            win32gui.ReleaseDC(self.hwnd, self.hdc)
            self.hdc = None




class Capture:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = int(width)
        self.height = int(height)
        self.hwnd = win32gui.GetDesktopWindow()
        self.srcdc = win32gui.GetWindowDC(self.hwnd)
        self.memdc = Gdi32.CreateCompatibleDC(self.srcdc)

        # 初始化 BitMapInfo 对象和数据缓冲区
        self._bmi = BitMapInfo()
        self._bmi.bmiHeader.biSize = ctypes.sizeof(BitMapInFader)
        self._bmi.bmiHeader.biPlanes = 1
        self._bmi.bmiHeader.biBitCount = 32
        self._bmi.bmiHeader.biCompression = 0
        self._bmi.bmiHeader.biClrUsed = 0
        self._bmi.bmiHeader.biClrImportant = 0
        self._bmi.bmiHeader.biWidth = self.width
        self._bmi.bmiHeader.biHeight = -self.height
        self._data = np.empty((self.height, self.width, 4), dtype=np.uint8)
        self.bmp = Gdi32.CreateCompatibleBitmap(self.srcdc, self.width, self.height)
        Gdi32.SelectObject(self.memdc, self.bmp)

    def cap(self):
        Gdi32.BitBlt(self.memdc, 0, 0, self.width, self.height, self.srcdc, self.x, self.y, 0x00CC0020)

        # 更新 BitMapInfo 对象的宽度和高度
        self._bmi.bmiHeader.biWidth = self.width
        self._bmi.bmiHeader.biHeight = -self.height

        Gdi32.GetDIBits(self.memdc, self.bmp, 0, self.height, self._data.ctypes.data, self._bmi, 0)
        return cv2.cvtColor(self._data.reshape(self.height, self.width), cv2.COLOR_BGRA2BGR)

