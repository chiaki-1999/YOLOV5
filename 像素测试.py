# --------------------------
# -*- coding: utf-8 -*-
# Bilibi   : 随风而息
# @Time    : 2022/9/27 22:44
# -----------------------

import time
from cmath import *
from ctypes import *

from win32api import GetAsyncKeyState

'''  --- 自用像素测试 ---'''


def HFOV_test(a=0, b=1000, c=10):  # a:初始值，b：右移多少像素，c:左移像素
    print('---- HFOV测试 ----')
    print('→移动{},←移动{},HOME完成测试，测试开始...'.format(b, c))
    mouse(int(0), int(0))  # 预热
    time.sleep(0.1)
    while True:
        if GetAsyncKeyState(0x24):
            return a
        if GetAsyncKeyState(0x27) and mouse(int(b), int(0)):
            a += b
            print('\rX: {}'.format(a), end='')
            time.sleep(0.5)
        elif GetAsyncKeyState(0x25) and mouse(int(-c), int(0)):
            a -= c
            print('\rX: {}'.format(a), end='')
            time.sleep(0.5)


def VFOV_test(a=0, b=1000, c=10):  # a:初始值，b：上移多少像素，c:下移像素
    print('---- VFOV测试 ----')
    print('↑移动{},↓移动{},HOME完成测试，测试开始...'.format(b, c))
    mouse(int(0), int(0))  # 预热
    time.sleep(0.1)
    while True:
        if GetAsyncKeyState(0x24):
            return a
        if GetAsyncKeyState(0x27) and mouse(int(), int(b)):
            a += b
            print('\rY: {}'.format(a), end='')
            time.sleep(0.5)
        elif GetAsyncKeyState(0x25) and mouse(int(0), int(-c)):
            a -= c
            print('\rY: {}'.format(a), end='')
            time.sleep(0.5)


if __name__ == '__main__':
    while True:
        ip = input('0:HFOV or 1:VFOV，END退出 >>>')
        if ip == '0':
            print('总的X像素:{}'.format(HFOV_test()))
        elif ip == '1':
            print('总的Y像素:{}'.format(VFOV_test()))
        elif GetAsyncKeyState(0x23):
            break


class MouseInput(Structure):
    _fields_ = [("dx", c_long),
                ("dy", c_long),
                ("mouseData", c_ulong),
                ("dwFlags", c_ulong),
                ("time", c_ulong),
                ("dwExtraInfo", POINTER(c_ulong))]


# SendInput结构体
class Input_I(Union):
    _fields_ = [("mi", MouseInput)]


# SendInput结构体
class INPUT(Structure):
    _fields_ = [("type", c_ulong),
                ("inp_i", Input_I)]


# SendInput 移动
def mouse(x, y):
    inp_i = Input_I()
    inp_i.mi = MouseInput(x, y, 0, 0x0001, 0, pointer(c_ulong(0)))
    input_m = INPUT(0, inp_i)
    if windll.user32.SendInput(1, pointer(input_m), sizeof(input_m)) == 0:
        return False
    else:
        return True


# HFOV
def HFOV(input_x, args):
    x = (args.game_width / 2) / tan(args.game_HFOV * pi / 180 / 2)
    return (atan(input_x / x)) * (args.game_x_pixel / (2 * pi))


# VFOV
def VFOV(input_y, args):
    y = (args.game_height / 2) / tan((args.game_VFOV * pi) / 180 / 2)
    return (atan(input_y / y)) * (args.game_y_pixel / pi)
