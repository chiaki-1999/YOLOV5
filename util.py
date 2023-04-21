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


def calc_angle_pixels(sub_s, fov, pixels, size):
    fov_radians = math.radians(fov)
    unit_angle_pixels = pixels / math.radians(size)
    filming_distance = size / 2 / math.tan(fov_radians / 2)
    rotation_angle = math.atan(sub_s / filming_distance)
    convert_mobile_pixels = rotation_angle * unit_angle_pixels
    return convert_mobile_pixels


PIXEL_X = 5650
PIXEL_Y = 2750
WIDTH = 2560
HEIGHT = 1440
FOV_X = 84
FOV_Y = 53


def HOV_new(sub_s):
    return calc_angle_pixels(sub_s, FOV_X, PIXEL_X, 360)


def OVF_new(sub_s):
    return calc_angle_pixels(sub_s, FOV_Y, PIXEL_Y, 180)




def HFOV(input_x):
    x = (WIDTH / 2) / math.tan(FOV_X * math.pi / 180 / 2)
    return (math.atan(input_x / x)) * (PIXEL_X / (2 * math.pi))


# VFOV
def VFOV(input_y):
    y = (HEIGHT / 2) / math.tan((FOV_Y * math.pi) / 180 / 2)
    return (math.atan(input_y / y)) * (PIXEL_Y / math.pi)


class PID(object):
    def __init__(self, exp_val, P: float, I: float, D: float):
        self.Kp = P
        self.Ki = I
        self.Kd = D

        self.PIDOutput = 0.0  # PID控制器输出
        self.SystemOutput = 0.0  # 系统输出值
        self.LastSystemOutput = 0.0  # 系统的上一次输出

        self.Error = 0.0
        self.LastError = 0.0
        self.LastLastError = 0.0

    # 设置PID控制器参数
    def cmd_pid(self, sub_s):

        self.Error = sub_s - self.SystemOutput
        # 计算增量
        IncrementalValue = self.Kp * (self.Error - self.LastError) \
                           + self.Ki * self.Error + self.Kd * (self.Error - 2 * self.LastError + self.LastLastError)
        # 计算输出
        self.PIDOutput += IncrementalValue
        self.LastLastError = self.LastError
        self.LastError = self.Error
        return self.PIDOutput

