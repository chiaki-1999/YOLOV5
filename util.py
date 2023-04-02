from win32con import SPI_GETMOUSE, SPI_SETMOUSE, SPI_GETMOUSESPEED, SPI_SETMOUSESPEED
from sys import exit
from platform import release
from ctypes import windll
from math import atan
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


# 简易FOV计算
def FOV(target_move, base_len):
    actual_move = atan(target_move / base_len) * base_len  # 弧长
    return actual_move


# 尝试pid
class PID:
    def __init__(self, P=0.2, I=0.0, D=0.0, exp_value=0.0):
        self.kp = P
        self.ki = I
        self.kd = D
        self.uPrevious = 0
        self.uCurent = 0
        self.setValue = exp_value
        self.lastErr = 0
        self.preLastErr = 0
        self.errSum = 0
        self.errSumLimit = 10

    # 位置式PID
    def pid_position(self, curValue):
        err = self.setValue - curValue
        dErr = err - self.lastErr
        self.preLastErr = self.lastErr
        self.lastErr = err
        self.errSum += err
        outPID = self.kp * err + (self.ki * self.errSum) + (self.kd * dErr)
        return outPID

    # 增量式PID
    def __call__(self, curValue):
        self.uCurent = self.pid_position(curValue)  # 用位置式记录位置
        outPID = self.uCurent - self.uPrevious
        self.uPrevious = self.uCurent
        return outPID

    # 更新比例P值
    def set_p(self, new_p):
        self.kp = new_p
