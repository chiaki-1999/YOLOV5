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


# 简易FOV计算
def FOV(target_move, base_len):
    actual_move = atan(target_move / base_len) * base_len  # 弧长
    return actual_move


# 确认窗口句柄与类名
def get_window_info():
    supported_games = 'Valve001 CrossFire LaunchUnrealUWindowsClient LaunchCombatUWindowsClient UnrealWindow UnityWndClass'
    test_window = 'Notepad3 PX_WINDOW_CLASS Notepad Notepad++'
    emulator_window = 'BS2CHINAUI Qt5154QWindowOwnDCIcon LSPlayerMainFrame TXGuiFoundation Qt5QWindowIcon LDPlayerMainFrame'
    class_name, hwnd_var = None, None
    testing_purpose = False
    while not hwnd_var:  # 等待游戏窗口出现
        milli_sleep(3000)
        try:
            hwnd_active = win32gui.GetForegroundWindow()
            class_name = win32gui.GetClassName(hwnd_active)
            if class_name not in (supported_games + test_window + emulator_window):
                print('请使支持的游戏/程序窗口成为活动窗口...')
                continue
            else:
                outer_hwnd = hwnd_var = win32gui.FindWindow(class_name, None)
                if class_name in emulator_window:
                    hwnd_var = win32gui.FindWindowEx(hwnd_var, None, None, None)
                elif class_name in test_window:
                    testing_purpose = True
                print('已找到窗口')
        except pywintypes.error:
            print('您可能正使用沙盒,目前不支持沙盒使用')
            exit(0)

    return class_name, hwnd_var, outer_hwnd, testing_purpose
