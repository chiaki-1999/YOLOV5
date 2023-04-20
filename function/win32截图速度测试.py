import numpy as np
import win32gui
import win32ui


class Capture:
    hwnd = None
    x, y, w, h = None, None, None, None

    def __init__(self):
        self.cDC = None
        self.dcObj = None
        self.wDC = None

    def Init(self, hwnd, w, h):
        self.hwnd = hwnd
        self.w, self.h = w, h
        # 获取窗口数据
        window_rect = win32gui.GetWindowRect(hwnd)
        client_rect = win32gui.GetClientRect(hwnd)
        left_corner = win32gui.ClientToScreen(hwnd, (0, 0))
        # 确认截图相关数据
        total_w = client_rect[2] - client_rect[0]
        total_h = client_rect[3] - client_rect[1]
        self.x = (total_w - w) // 2 + left_corner[0] - window_rect[0]
        self.y = (total_h - h) // 2 + left_corner[1] - window_rect[1]
        self.wDC = win32gui.GetWindowDC(self.hwnd)
        self.dcObj = win32ui.CreateDCFromHandle(self.wDC)
        self.cDC = self.dcObj.CreateCompatibleDC()

    def InitEx(self, hwnd, x, y, w, h):
        self.hwnd = hwnd
        self.x, self.y, self.w, self.h = x, y, w, h
        self.wDC = win32gui.GetWindowDC(self.hwnd)
        self.dcObj = win32ui.CreateDCFromHandle(self.wDC)
        self.cDC = self.dcObj.CreateCompatibleDC()

    def capture(self):
        try:
            dataBitMap = win32ui.CreateBitmap()
            dataBitMap.CreateCompatibleBitmap(self.dcObj, self.w, self.h)
            self.cDC.SelectObject(dataBitMap)
            self.cDC.BitBlt((0, 0), (self.w, self.h), self.dcObj, (self.x, self.y), 0x00CC0020)
            # 转换使得opencv可读
            signedIntsArray = dataBitMap.GetBitmapBits(True)
            cut_img = np.frombuffer(signedIntsArray, dtype='uint8')
            cut_img.shape = (self.h, self.w, 4)
            cut_img = cut_img[..., :3]  # 去除alpha
            win32gui.DeleteObject(dataBitMap.GetHandle())  # 释放资源
            cut_img = np.ascontiguousarray(cut_img)
            return cut_img
        except:
            print('erro\n')
            return None

    def release_resource(self):
        win32gui.DeleteObject(self.wDC.GetHandle())
        self.wDC, self.dcObj, self.cDC = None, None, None
