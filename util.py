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


def calculate_pixel_move(delta_x, delta_y):
    FOV_X = 106.260205
    FOV_Y = 73.739795

    PIXEL_X = 6547
    PIXEL_Y = 3228

    WIDTH = 1920
    HEIGHT = 1080

    PIXEL_RAD_X = PIXEL_X / (2 * math.pi)
    PIXEL_RAD_Y = PIXEL_Y / math.pi

    SUP_DISTANCE_X = (WIDTH / 2) / math.tan((FOV_X * math.pi / 180) / 2)
    SUP_DISTANCE_Y = (HEIGHT / 2) / math.tan((FOV_Y * math.pi / 180) / 2)

    target_move_x = math.atan(abs(delta_x) / SUP_DISTANCE_X) * PIXEL_RAD_X
    target_move_y = math.atan(abs(delta_y) / SUP_DISTANCE_Y) * PIXEL_RAD_Y

    return -target_move_x if delta_x < 0 else target_move_x, -target_move_y if delta_y < 0 else target_move_y


class PID(object):
    def __init__(self, kp, ki, kd, imax, dt, error_threshold):
        self.Kp = kp
        self.Ki = ki
        self.Kd = kd
        self.imax = imax
        self.total_error = 0
        self.last_output = 0
        self.last_error = 0
        self.dt = dt
        self.error_threshold = error_threshold
        self.last_error_sign = None
        self.iterations_since_last_change = 0

    def cmd_pid(self, err):
        # 更新总误差
        self.total_error += err * self.dt
        self.total_error = max(min(self.total_error, self.imax), -self.imax)

        # 更新输出值
        d_err = (err - self.last_error) / self.dt
        self.last_output = self.Kp * err + self.Ki * self.total_error + self.Kd * d_err

        # 动态调整 PID 参数
        if abs(err) > self.error_threshold:
            # 如果误差符号发生变化，则重新开始计数
            if self.last_error_sign is None or (err >= 0) != (self.last_error_sign >= 0):
                self.last_error_sign = 1 if err >= 0 else -1
                self.iterations_since_last_change = 0
            else:
                self.iterations_since_last_change += 1

            # 根据计数和误差符号调整 PID 参数
            if self.iterations_since_last_change == 0:
                self.Kp *= 0.8
                self.Ki *= 0.1
                self.Kd *= 0.01
            elif self.iterations_since_last_change == 1:
                self.Kp *= 0.6
                self.Ki *= 0.2
                self.Kd *= 0.01
            elif self.iterations_since_last_change == 2:
                self.Kp *= 0.4
                self.Ki *= 0.2
                self.Kd *= 0.01
            else:
                self.Kp *= 0.2
                self.Ki *= 0.2
                self.Kd *= 0.01

        # 更新误差值
        self.last_error = err

        return self.last_output



