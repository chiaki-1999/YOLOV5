import math
from ctypes import windll
from platform import release
from sys import exit

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


PIXEL_X = 5650
PIXEL_Y = 2750
WIDTH = 2560
HEIGHT = 1440
FOV_X = 84
FOV_Y = 53


def HFOV(input_x):
    x = (WIDTH / 2) / math.tan(FOV_X * math.pi / 180 / 2)
    return (math.atan(input_x / x)) * (PIXEL_X / (2 * math.pi))


# VFOV
def VFOV(input_y):
    y = (HEIGHT / 2) / math.tan((FOV_Y * math.pi) / 180 / 2)
    return (math.atan(input_y / y)) * (PIXEL_Y / math.pi)

