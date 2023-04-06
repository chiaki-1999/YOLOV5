import numpy as np
import win32gui
import win32ui


class GrabScreen:
    def __init__(self, hwnd=None, x=None, y=None, w=None, h=None):
        self.hwnd = hwnd
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.cdc = None
        self.dco = None
        self.wdc = None

    def init(self, hwnd, w, h):
        self.hwnd = hwnd
        self.w, self.h = w, h
        window_rect = win32gui.GetWindowRect(hwnd)
        client_rect = win32gui.GetClientRect(hwnd)
        left_corner = win32gui.ClientToScreen(hwnd, (0, 0))
        total_w = client_rect[2] - client_rect[0]
        total_h = client_rect[3] - client_rect[1]
        self.x = (total_w - w) // 2 + left_corner[0] - window_rect[0]
        self.y = (total_h - h) // 2 + left_corner[1] - window_rect[1]
        self.wdc = win32gui.GetWindowDC(self.hwnd)
        self.dco = win32ui.CreateDCFromHandle(self.wdc)
        self.cdc = self.dco.CreateCompatibleDC()

    def capture(self):
        for _ in range(3):
            try:
                data_bitmap = win32ui.CreateBitmap()
                data_bitmap.CreateCompatibleBitmap(self.dco, self.w, self.h)
                self.cdc.SelectObject(data_bitmap)
                self.cdc.BitBlt((0, 0), (self.w, self.h), self.dco, (self.x, self.y), SRCCOPY)
                signed_ints_array = data_bitmap.GetBitmapBits(True)
                cut_img = np.frombuffer(signed_ints_array, dtype='uint8')
                cut_img.shape = (self.h, self.w, 4)
                cut_img = cut_img[..., :3]
                win32gui.DeleteObject(data_bitmap.GetHandle())
                cut_img = np.ascontiguousarray(cut_img)
                return cut_img
            except Exception as e:
                print(f'Capture error: {e}')
                self.release_resource()
        return None

    def release_resource(self):
        if self.wdc:
            win32gui.ReleaseDC(self.hwnd, self.wdc)
            self.wdc = None
        if self.dco:
            self.dco.DeleteDC()
            self.dco = None
        if self.cdc:
            self.cdc.DeleteDC()
            self.cdc = None
