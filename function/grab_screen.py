import cv2
import numpy as np
import win32api
import win32con
import win32gui
import win32print
import win32ui


def win32_capture(grab_info):
    hwnd = 0
    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)

    gx, gy, gs = grab_info
    gw = gs
    gh = gs

    img = np.zeros((gh, gw, 3), dtype=np.uint8)

    for y in range(gh):
        for x in range(gw):
            color = win32gui.GetPixel(mfcDC.GetSafeHdc(), gx + x, gy + y)
            img[y, x] = (color & 0xFF, (color >> 8) & 0xFF, (color >> 16) & 0xFF)

    mfcDC.DeleteDC()
    return cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)

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
        top_x, top_y = int(top_x + x // 2 * (1 - 0.4)), int(top_y + y // 2 * (1 - 0.4))
        _inspection_size = top_x, top_y, len_x, len_y
    return _inspection_size
