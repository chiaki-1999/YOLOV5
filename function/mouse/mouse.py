import ctypes
import os

try:
    root = os.path.abspath(os.path.dirname(__file__))
    driver = ctypes.CDLL(f'{root}/mouse.dll')
    ok = driver.device_open() == 1  # 该驱动每个进程可打开一个实例
    if not ok:
        print('Error, GHUB or LGS driver not found')
except FileNotFoundError:
    print(f'Error, DLL file not found')
os.system('cls')


class Mouse:
    class mouse:

        """
        code: 1:左键, 2:中键, 3:右键
        """

        @staticmethod
        def press(code):
            if not ok:
                return
            driver.mouse_down(code)

        @staticmethod
        def release(code):
            if not ok:
                return
            driver.mouse_up(code)

        @staticmethod
        def click(code):
            if not ok:
                return
            driver.mouse_down(code)
            driver.mouse_up(code)

        @staticmethod
        def scroll(a):
            """
            a:没搞明白
            """
            if not ok:
                return
            driver.scroll(a)

        @staticmethod
        def move(x, y):
            """
            相对移动, 绝对移动需配合 pywin32 的 win32gui 中的 GetCursorPos 计算位置
            x: 水平移动的方向和距离, 正数向右, 负数向左
            y: 垂直移动的方向和距离
            """
            if not ok:
                return
            if x == 0 and y == 0:
                return
            driver.moveR(x, y, True)

    class keyboard:

        """
        键盘按键函数中，传入的参数采用的是键盘按键对应的键码
        code: 'a'-'z':A键-Z键, '0'-'9':0-9, 其他的没猜出来
        """

        @staticmethod
        def press(code):

            if not ok:
                return
            driver.key_down(code)

        @staticmethod
        def release(code):
            if not ok:
                return
            driver.key_up(code)

        @staticmethod
        def click(code):
            if not ok:
                return
            driver.key_down(code)
            driver.key_up(code)


"""
键盘按键和键盘对应代码表:
数字键盘 1 <--------> 96 数字键盘 2 <--------> 97 数字键盘 3 <--------> 98
数字键盘 4 <--------> 99 数字键盘 5 <--------> 100 数字键盘 6 <--------> 101
数字键盘 7 <--------> 102 数字键盘 8 <--------> 103 数字键盘 9 <--------> 104
数字键盘 0 <--------> 105
乘号 <--------> 106 加号 <--------> 107 Enter <--------> 108 减号 <--------> 109
小数点 <--------> 110 除号 <--------> 111
F1 <--------> 112 F2 <--------> 113 F3 <--------> 114 F4 <--------> 115
F5 <--------> 116 F6 <--------> 117 F7 <--------> 118 F8 <--------> 119
F9 <--------> 120 F10 <--------> 121 F11 <--------> 122 F12 <--------> 123
F13 <--------> 124 F14 <--------> 125 F15 <--------> 126
Backspace <--------> 8
Tab <--------> 9
Clear <--------> 12
Enter <--------> 13
Shift <--------> 16
Control <--------> 17
Alt <--------> 18
Caps Lock <--------> 20
Esc <--------> 27
空格键 <--------> 32
Page Up <--------> 33
Page Down <--------> 34
End <--------> 35
Home <--------> 36
左箭头 <--------> 37
向上箭头 <--------> 38
右箭头 <--------> 39
向下箭头 <--------> 40
Insert <--------> 45
Delete <--------> 46
Help <--------> 47
Num Lock <--------> 144
; : <--------> 186
= + <--------> 187
- _ <--------> 189
/ ? <--------> 191
` ~ <--------> 192
[ { <--------> 219
| <--------> 220
] } <--------> 221
'' ' <--------> 222
"""