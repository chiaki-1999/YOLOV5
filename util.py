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


PIXEL_X = 2825
PIXEL_Y = 1375
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


class PIDController:
    def __init__(self, Kp, Ki, Kd):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.last_error = 0
        self.integral = 0

    def reset(self):
        self.last_error = 0
        self.integral = 0

    def update_pid(self, Kp=None, Ki=None, Kd=None):
        if Kp is not None:
            self.Kp = Kp
        if Ki is not None:
            self.Ki = Ki
        if Kd is not None:
            self.Kd = Kd

    def compute(self, point, current_value, dt):
        error = point - current_value
        self.integral += error * dt
        derivative = (error - self.last_error) / dt
        output = self.Kp * error + self.Ki * self.integral + self.Kd * derivative
        self.last_error = error
        return output


# pid实例
