import win32api
import win32con
import win32gui
import win32print

from function.readini import screen_info
from function.win32截图速度测试 import Capture

gx, gy, gs = screen_info
WindowName = ['CrossFire', 'Apex']
hwnd = 0

Cp = Capture()


def win32_capture_Init():
    global hwnd
    for name in WindowName:
        handle = win32gui.FindWindow(None, name)
        if handle:
            hwnd = handle
            break
    Cp.InitEx(hwnd, gx, gy, gs, gs)


def win32_capture():
    return Cp.capture()


###获取真实的分辨率
def get_real_screen_resolution():
    h_DC = win32gui.GetDC(0)
    width = win32print.GetDeviceCaps(h_DC, win32con.DESKTOPHORZRES)
    height = win32print.GetDeviceCaps(h_DC, win32con.DESKTOPVERTRES)
    return {"width": width, "height": height}


###获取屏幕的缩放比例
def get_screen_scale():
    real_resolution = get_real_screen_resolution()
    screen_size = get_screen_size()
    proportion = round(real_resolution['width'] / screen_size['width'], 2)
    return proportion


# Memoize the screen size
_screen_size = None


def get_screen_size():
    global _screen_size
    if _screen_size is None:
        _screen_size = (win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1))
    return _screen_size


_inspection_size = None


def get_inspection_size():
    global _inspection_size
    if _inspection_size is None:
        width, height = get_screen_size()
        top_x, top_y = 0, 0
        len_x, len_y = int(width * 0.4), int(height * 0.4)
        top_x, top_y = int(top_x + width // 2 * (1 - 0.4)), int(top_y + height // 2 * (1 - 0.4))
        _inspection_size = top_x, top_y, len_x, len_y
    return _inspection_size
