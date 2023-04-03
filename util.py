from ctypes import windll
from math import atan
from platform import release
from sys import exit

import pywintypes
import win32gui

# 预加载为睡眠函数做准备
TimeBeginPeriod = windll.winmm.timeBeginPeriod
HPSleep = windll.kernel32.Sleep
TimeEndPeriod = windll.winmm.timeEndPeriod


# 高DPI感知
def set_dpi():
    if int(release()) >= 7:
        try:
            windll.shcore.SetProcessDpiAwareness(1)
        except AttributeError:
            windll.user32.SetProcessDPIAware()
    else:
        exit(0)


# 检查是否为管理员权限
def is_admin():
    try:
        return windll.shell32.IsUserAnAdmin()
    except OSError as err:
        print('OS error: {0}'.format(err))
        return False


# 比起python自带sleep稍微精准的睡眠
def milli_sleep(num):
    TimeBeginPeriod(1)
    HPSleep(int(num))  # 减少报错
    TimeEndPeriod(1)

