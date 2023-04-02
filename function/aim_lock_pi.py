from ctypes import *
from math import *

u32 = windll.user32


class Locker(object):
    def __init__(self):
        self.head_first = True
        self.locked = False
        self.lock_sen = 1
        self.lock_tag = [1, 0]
        self.lock_smooth = 3
        self.Kp, self.Ki, self.Kd = 0.4, 0.02, 0
        self.error_sum_x = 0
        self.error_sum_y = 0
        self.pre_error_x = 0
        self.pre_error_y = 0
        self.previous = None
        self.top_x = 0
        self.top_y = 0
        self.len_x = 0
        self.len_y = 0
        self.shot_time = 0

    def __pid(self, error_x, error_y):
        # 离散形式PID
        Pout_x = self.Kp * error_x
        self.error_sum_x += error_x
        Iout_x = self.Ki * self.error_sum_x
        Dout_x = self.Kd * (error_x - self.pre_error_x)
        self.pre_error_x = error_x

        Pout_y = self.Kp * error_y
        self.error_sum_y += error_y
        Iout_y = self.Ki * self.error_sum_y
        Dout_y = self.Kd * (error_y - self.pre_error_y)
        self.pre_error_y = error_y
        return int(Pout_x + Iout_x + Dout_x), int(Pout_y + Iout_y + Dout_y)

    def reset_params(self):  # 重置参数
        self.error_sum_x = 0
        self.error_sum_y = 0
        self.pre_error_x = 0
        self.pre_error_y = 0
        self.previous = None
        self.locked = False

    def lock(self, aims, pos_center):  # 开锁
        print("self.previous : ", self.previous)
        mouse_x, mouse_y = pos_center
        aims_copy = aims.copy()  # aims = [[tag, x_center, y_center, width, height],.....]
        if len(aims_copy):
            dist_list = []
            tag_list = [x[5] for x in aims_copy]
            if self.previous is not None:
                if self.previous in tag_list:  # 重复目标
                    aims_copy = [aim for aim in aims_copy if self.previous in aim]
            for det in aims_copy:
                _, x_c, y_c, _, _, _ = det
                dist = (self.len_x * float(x_c) + self.top_x - mouse_x) ** 2 + (
                        self.len_y * float(y_c) + self.top_y - mouse_y) ** 2
                dist_list.append(dist)
            det = aims_copy[dist_list.index(min(dist_list))]  # 取最小距离
            tag, x_center, y_center, width, height, target = det
            print("det  : ", det)
            self.previous = target
            x_center, width = self.len_x * float(x_center) + self.top_x, self.len_x * float(width)
            y_center, height = self.len_y * float(y_center) + self.top_y, self.len_y * float(height)

            theta_x = atan((mouse_x - x_center) / 640) * 180 / pi
            theta_y = atan((mouse_y - y_center) / 640) * 180 / pi
            x = (theta_x / self.lock_sen) / 0.022
            y = (theta_y / self.lock_sen) / 0.03
            if self.lock_smooth > 1.00:  # lock平滑系数
                rel_x = 0.
                rel_y = 0.
                if rel_x > x:
                    rel_x += 1. + (x / self.lock_smooth)
                elif rel_y < x:
                    rel_x -= 1. - (x / self.lock_smooth)
                if rel_y > y:
                    rel_y += 1. + (y / self.lock_smooth)
                elif rel_y < y:
                    rel_y -= 1. - (y / self.lock_smooth)
            else:
                rel_x = x
                rel_y = y

            rel_x, rel_y = self.__pid(rel_x, rel_y)

            print(" rel_x : ", rel_x, "rel_y : ", rel_y)
            return -rel_x, -rel_y  # 移动鼠标
        else:
            return 0, 0
