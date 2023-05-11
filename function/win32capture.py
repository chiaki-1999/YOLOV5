import numpy as np
import cv2
import win32gui
import win32ui
import win32con


class ScreenCapture:
    def __init__(self, x, y, width, height, hwnd):
        self.rect = (x, y, x + width, y + height)
        self.hwnd = hwnd

    def capture(self):
        srcdc = win32ui.CreateDCFromHandle(win32gui.GetDC(self.hwnd))
        memdc = srcdc.CreateCompatibleDC()
        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(srcdc, self.rect[2] - self.rect[0], self.rect[3] - self.rect[1])
        memdc.SelectObject(bmp)
        memdc.BitBlt((0, 0), (self.rect[2] - self.rect[0], self.rect[3] - self.rect[1]), srcdc, self.rect,
                     win32con.SRCCOPY)
        bmpstr = bmp.GetBitmapBits(True)
        img = np.frombuffer(bmpstr, dtype=np.uint8).reshape(
            (self.rect[3] - self.rect[1], self.rect[2] - self.rect[0], 4))[:, :, :3].astype(np.uint8)
        return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
