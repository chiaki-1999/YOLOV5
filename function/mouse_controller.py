import csv
import os
import random
import sys
import time
import uuid
from pathlib import Path
from queue import Empty
from threading import Thread

import winsound
from PyQt5.QtWidgets import QApplication, QMainWindow
from pynput import mouse

from ShowUI import Ui_MainWindow
from function.mouse.mouse import Mouse
from util import PID, fov_y, fov_x

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
info_dir = ROOT / 'information.csv'
with open(info_dir, 'r', encoding='utf-8', newline='') as fr:
    reader = csv.DictReader(fr)
    for r in reader:
        pass
    screen_size = r['screen_size']
fr.close()

mouse_left_click = False
mouse_right_click = False
mouses_offset_ratio = 1
flag_lock_obj_left = False
flag_lock_obj_right = False
offset_pixel_center = 3
offset_pixel_y = 0.3
grab_size = 640
shun_ju = False
last_fire_time = time.monotonic()
mouses = mouse.Controller()
is_sleep = True
out_check = 0

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
info_dir = os.path.join(ROOT, 'information.csv')
with open(info_dir, 'r', encoding='utf-8', newline='') as fr:
    reader = csv.DictReader(fr)
    for r in reader:
        pass
    screen_size = r['screen_size']
fr.close()

screen_size = screen_size.split('*')
screen_size = (int(screen_size[0]), int(screen_size[1]))

screen_width, screen_height = screen_size
grab = (int((screen_size[0] - grab_size) / 2), int((screen_size[1] - grab_size) / 2), grab_size, grab_size)
grab_x, grab_y, grab_width, grab_height = grab
pos_center = (int(screen_width / 2), int(screen_height / 2))
max_pos = int(pow((pow(pos_center[0], 2) + pow(pos_center[1], 2)), 0.5))
mouse_x, mouse_y = pos_center

mouses = mouse.Controller()

kp = 0.3  # 比例系数
ki = 0.02  # 积分系数
kd = 0.01  # 微分系数


def track_target_ratio(box_lists, offset_ratio, dt):
    global mouse_x, mouse_y
    if not box_lists:
        return 0, 0, 0

    closest_box = None
    min_dist = float("inf")
    for box in box_lists:
        x_target = int(box[1] * grab_width + grab_x)
        y_target = int(box[2] * grab_height + grab_y)
        dist = ((x_target - pos_center[0]) ** 2 + (y_target - pos_center[1]) ** 2)
        offset = int(box[4] * grab_height * offset_ratio)
        if dist < min_dist:
            min_dist = dist
            closest_box = box
            mouse_x = x_target - pos_center[0]
            mouse_y = y_target - pos_center[1] - offset

    if closest_box is None:
        return 0, 0, 0
    mouse_x = fov_x(mouse_x)
    mouse_y = fov_y(mouse_y)
    pid_x = PID(kp, ki, kd, 20, dt, 10).cmd_pid(int(mouse_x))
    pid_y = PID(kp, ki, kd, 20, dt, 10).cmd_pid(int(mouse_y))
    return pid_x, pid_y, 1


def usb_control(usb, kill):
    global mouse_left_click, mouse_right_click, mouses_offset_ratio, offset_pixel_center, offset_pixel_y, out_check, \
        flag_lock_obj_right, flag_lock_obj_left
    ui_show = Thread(target=show_ui)
    ui_show.start()
    listener_mouse = mouse.Listener(on_click=on_click)
    listener_mouse.start()

    while True:
        kill.value = out_check
        try:
            data = usb.get(timeout=0.01)
        except Empty:
            continue
        zb = time.time()
        box_lists, last_time = data
        pos_min_x, pos_min_y, has_target = track_target_ratio(box_lists, offset_pixel_y, time.time() - last_time)
        if ((mouse_left_click and flag_lock_obj_left)
            or (mouse_right_click and flag_lock_obj_right)) \
                and has_target:
            Mouse.mouse.move(int(pos_min_x * mouses_offset_ratio), int(pos_min_y * mouses_offset_ratio))
            print(" 计算坐标 ： {:.2f} ms".format((time.time() - zb) * 1000))


def auto_fire():
    global is_sleep, last_fire_time
    now = time.monotonic()
    if is_sleep:
        if now - last_fire_time >= 0.13:
            Mouse.mouse.click(1)
            last_fire_time = now
            is_sleep = False
    else:
        time.sleep(0.13)
        is_sleep = True


def show_ui():
    app = QApplication([])
    windows = ShowWindows()
    windows.show()
    app.exec_()


def on_click(x, y, button, pressed):
    global mouse_left_click, mouse_right_click, flag_lock_obj_left, flag_lock_obj_right
    if button == mouse.Button.left:
        mouse_left_click = pressed
    elif button == mouse.Button.right:
        mouse_right_click = pressed


class ShowWindows(QMainWindow):
    def __init__(self):
        global mouses_offset_ratio, offset_pixel_center, offset_pixel_y
        super(ShowWindows, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.horizontalSlider.setMinimum(0)
        self.ui.horizontalSlider.setMaximum(10)
        self.ui.horizontalSlider.setSingleStep(1)
        self.ui.label_12.setText(str(mouses_offset_ratio))
        self.ui.horizontalSlider.valueChanged.connect(self.valueChange_1)

        self.ui.horizontalSlider_2.setMinimum(4)
        self.ui.horizontalSlider_2.setMaximum(12)
        self.ui.horizontalSlider_2.setSingleStep(1)
        self.ui.label_13.setText(str(offset_pixel_center))
        self.ui.horizontalSlider_2.valueChanged.connect(self.valueChange_2)

        self.ui.horizontalSlider_3.setMinimum(-40)
        self.ui.horizontalSlider_3.setMaximum(40)
        self.ui.horizontalSlider_3.setSingleStep(1)
        self.ui.label_14.setText(str(offset_pixel_y))
        self.ui.horizontalSlider_3.valueChanged.connect(self.valueChange_3)

        self.ui.checkBox.stateChanged.connect(self.boxChange_1)
        self.ui.checkBox_2.stateChanged.connect(self.boxChange_2)
        self.ui.checkBox_3.stateChanged.connect(self.boxChange_3)

        self.ui.pushButton_3.clicked.connect(self.outButton)

    def valueChange_1(self):
        global mouses_offset_ratio
        mouses_offset_ratio = round(self.ui.horizontalSlider.value() / 10, 1)
        self.ui.label_12.setText(str(mouses_offset_ratio))

    def valueChange_2(self):
        global offset_pixel_center
        offset_pixel_center = self.ui.horizontalSlider_2.value()
        self.ui.label_13.setText(str(offset_pixel_center))

    def valueChange_3(self):
        global offset_pixel_y
        offset_pixel_y = round(self.ui.horizontalSlider_3.value() / 100, 2)
        self.ui.label_14.setText(str(offset_pixel_y))

    def boxChange_1(self):
        global flag_lock_obj_left
        flag_lock_obj_left = self.ui.checkBox.isChecked()
        if flag_lock_obj_left:
            self.ui.label_2.setText('启动状态（Open）')
        else:
            self.ui.label_2.setText('启动状态（Close）')
        winsound.Beep(600, 200)

    def boxChange_2(self):
        global flag_lock_obj_right
        flag_lock_obj_right = self.ui.checkBox_2.isChecked()
        if flag_lock_obj_right:
            self.ui.label_2.setText('启动状态（Open）')
        else:
            self.ui.checkBox_3.setChecked(False)
            self.ui.label_2.setText('启动状态（Close）')
        winsound.Beep(600, 200)

    def boxChange_3(self):
        global shun_ju
        shun_ju = self.ui.checkBox_3.isChecked()
        if shun_ju:
            self.ui.checkBox_2.setChecked(True)
            self.ui.label_2.setText('启动状态（Open）')
        else:
            self.ui.label_2.setText('启动状态（Close）')
        winsound.Beep(600, 200)

    # 程序退出
    def outButton(self):
        global out_check
        winsound.Beep(600, 200)
        out_check = 1
        self.close()
