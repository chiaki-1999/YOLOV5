import math
import statistics
from ctypes import windll
from platform import release
from sys import exit

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


def get_window_info():
    # 获取窗口句柄和类名
    hwnd_var = win32gui.GetForegroundWindow()
    class_name = win32gui.GetClassName(hwnd_var)

    # 获取窗口客户端矩形和左上角坐标
    if "last_hwnd_var" in get_window_info.__dict__ and get_window_info.last_hwnd_var == hwnd_var:
        window_rect, client_rect, left_corner = get_window_info.last_window_rect, get_window_info.last_client_rect, \
            get_window_info.last_left_corner
    else:
        window_rect = win32gui.GetWindowRect(hwnd_var)
        client_rect = win32gui.GetClientRect(hwnd_var)
        left_corner = win32gui.ClientToScreen(hwnd_var, (0, 0))
        get_window_info.last_hwnd_var = hwnd_var
        get_window_info.last_window_rect, get_window_info.last_client_rect, get_window_info.last_left_corner = \
            window_rect, client_rect, left_corner

    # 确认窗口相关数据
    total_w, total_h = client_rect[2] - client_rect[0], client_rect[3] - client_rect[1]

    # 获取DPI缩放因子
    dpi_var = max(windll.user32.GetDpiForWindow(hwnd_var) / 96, 1.0)

    return class_name, hwnd_var, left_corner, total_w, total_h, dpi_var


def calculate_fov(target_move, base_len, total_w, total_h):
    # 计算FOV_X
    fov_x = 2 * (180 / 3.14) * math.atan((total_w / 2) / base_len)
    actual_move_x = math.atan(target_move[0] / base_len) * base_len
    fov_x *= actual_move_x / (total_w / 2)

    # 计算FOV_Y
    fov_y = 2 * (180 / 3.14) * math.atan((total_h / 2) / base_len)
    actual_move_y = math.atan(target_move[1] / base_len) * base_len
    fov_y *= actual_move_y / (total_h / 2)

    return fov_x, fov_y


PIXEL_X = 5650
PIXEL_Y = 2750
WIDTH = 2560
HEIGHT = 1440
FOV_X = 84.11
FOV_Y = 54


def fov_x(delta_x):
    per_pixel_rad = PIXEL_X / (2 * math.pi)
    delta_abs_x = abs(delta_x)
    sup_distance = (WIDTH / 2) / math.tan((FOV_X * math.pi / 180) / 2)
    target_angle_rad = math.atan(delta_abs_x / sup_distance)
    target_move = target_angle_rad * per_pixel_rad
    return (-1) * target_move if delta_x < 0 else target_move


def fov_y(delta_y):
    per_pixel_rad = PIXEL_Y / math.pi
    delta_abs_y = abs(delta_y)
    sup_distance = (HEIGHT / 2) / math.tan((FOV_Y * math.pi / 180) / 2)
    target_angle_rad = math.atan(delta_abs_y / sup_distance)
    target_move = target_angle_rad * per_pixel_rad
    return (-1) * target_move if delta_y < 0 else target_move



class PID:
    def __init__(self, p, i, d, set_value, sample_time):
        self.kp = p
        self.ki = i
        self.kd = d
        self.set_value = set_value  # 目标值
        self.last_error = 0  # 上一次误差
        self.pre_last_error = 0  # 临时存误差
        self.err_sum = 0  # 误差总和
        self.sample_time = sample_time
        self.last_output = None
        self.last_timestamp = None

    # 位置式PID
    def pid_position(self, cur_value, timestamp=None):
        # 计算时间间隔
        if timestamp is not None and self.last_timestamp is not None:
            dt = (timestamp - self.last_timestamp).total_seconds()
        else:
            dt = self.sample_time

        # 计算误差
        error = self.set_value - cur_value

        # 计算误差积分项
        self.err_sum += (error + self.last_error) / 2 * dt

        # 计算误差微分项
        if self.last_output is not None:
            d_error = (error - self.last_error) / dt
        else:
            d_error = 0

        # 计算控制量
        output = self.kp * error + self.ki * self.err_sum + self.kd * d_error

        # 保存变量
        self.last_error = error
        self.last_output = output
        self.last_timestamp = timestamp

        return output

    def update_set_value(self, kp, ki, kd):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.last_error = None
        self.pre_last_error = None
        self.err_sum = 0
        self.last_output = None
        self.last_timestamp = None
