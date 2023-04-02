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
    saveDC = mfcDC.CreateCompatibleDC()
    saveBitMap = win32ui.CreateBitmap()

    gx, gy, gs = grab_info
    gw = gs
    gh = gs

    saveBitMap.CreateCompatibleBitmap(mfcDC, gw, gh)
    saveDC.SelectObject(saveBitMap)

    saveDC.BitBlt((0, 0), (gw, gh), mfcDC, (gx, gy), win32con.SRCCOPY)
    signed_ints_array = saveBitMap.GetBitmapBits(True)
    img = np.frombuffer(signed_ints_array, dtype='uint8')
    img.shape = (gh, gw, 4)
    win32gui.DeleteObject(saveBitMap.GetHandle())
    mfcDC.DeleteDC()
    saveDC.DeleteDC()
    return cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)


###获取真实的分辨率
def get_real_screen_resolution():
    h_DC = win32gui.GetDC(0)
    width = win32print.GetDeviceCaps(h_DC, win32con.DESKTOPHORZRES)
    height = win32print.GetDeviceCaps(h_DC, win32con.DESKTOPVERTRES)
    return {"width": width, "height": height}


###获取缩放后的分辨率
def get_screen_size():
    width = win32api.GetSystemMetrics(0)
    height = win32api.GetSystemMetrics(1)
    return {"width": width, "height": height}


###获取屏幕的缩放比例
def get_screen_scale():
    real_resolution = get_real_screen_resolution()
    screen_size = get_screen_size()
    proportion = round(real_resolution['width'] / screen_size['width'], 2)
    return proportion
