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

kp = 0.4  # 比例系数
ki = 0.02  # 积分系数
kd = 0.01  # 微分系数
pid_x = PID(kp, ki, kd, 0, 0.1)
pid_y = PID(kp, kp, kp, 0, 0.1)


def track_target_ratio(box_lists, offset_ratio):
    global mouse_x, mouse_y
    if not box_lists:
        return 0, 0, 0

    min_dist = float("inf")
    for box in box_lists:
        x_target = int(box[1] * grab_width + grab_x)
        y_target = int(box[2] * grab_height + grab_y)
        dist = ((x_target - pos_center[0]) ** 2 + (y_target - pos_center[1]) ** 2)
        offset = int(box[4] * grab_height * offset_ratio)
        if dist < min_dist:
            min_dist = dist
            mouse_x = x_target - pos_center[0]
            mouse_y = y_target - pos_center[1] - offset

    if min_dist == float("inf"):
        return 0, 0, 0
    mouse_x = fov_x(mouse_x).real
    mouse_y = fov_y(mouse_y).real

    # Kalman filter
    z = np.array([[mouse_x], [mouse_y]])
    x = np.dot(kalman_filter.F, kalman_filter.x) + np.dot(kalman_filter.B, kalman_filter.u)
    P = np.dot(np.dot(kalman_filter.F, kalman_filter.P), kalman_filter.F.T) + kalman_filter.Q
    S = np.dot(np.dot(kalman_filter.H, P), kalman_filter.H.T) + kalman_filter.R
    K = np.dot(np.dot(P, kalman_filter.H.T), np.linalg.inv(S))
    y = z - np.dot(kalman_filter.H, x)
    x = x + np.dot(K, y)
    kalman_filter.x = x
    kalman_filter.P = np.dot(np.eye(4) - np.dot(K, kalman_filter.H), P)

    # PID control
    x_ctrl = pid_x.pid_position(kalman_filter.x[0][0], timestamp=time.time())
    y_ctrl = pid_y.pid_position(kalman_filter.x[1][0], timestamp=time.time())

    return x_ctrl, y_ctrl, 1



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
        pos_min_x, pos_min_y, has_target = track_target_ratio(box_lists, offset_pixel_y)
        if ((mouse_left_click and flag_lock_obj_left)
            or (mouse_right_click and flag_lock_obj_right)) \
                and has_target:
            Mouse.mouse.move(int(pos_min_x * mouses_offset_ratio), int(pos_min_y * mouses_offset_ratio))
            print(" 计算坐标 ： {:.2f} ms".format((time.time() - zb) * 1000))


def show_ui():
    app = QApplication([])
    windows = ShowWindows()
    windows.show()
    app.exec_()


def on_click(x, y, button, pressed):
    global mouse_left_click, mouse_right_click, flag_lock_obj_left, flag_lock_obj_right
    flag_lock_obj = False
    if button == mouse.Button.left:
        mouse_left_click = pressed
        flag_lock_obj = flag_lock_obj_left
    elif button == mouse.Button.right:
        mouse_right_click = pressed
        flag_lock_obj = flag_lock_obj_right

    if flag_lock_obj and not pressed:
        pid_x.update_set_value(kp, ki, kd)
        pid_y.update_set_value(kp, ki, kd)


class ShowWindows(QMainWindow):
    def __init__(self):
        global kp, ki, kd,  offset_pixel_y
        super(ShowWindows, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.horizontalSlider.setMinimum(0)
        self.ui.horizontalSlider.setMaximum(100)
        self.ui.horizontalSlider.setSingleStep(1)
        self.ui.label_12.setText(str(ki))
        self.ui.horizontalSlider.valueChanged.connect(self.valueChange_1)

        self.ui.horizontalSlider_2.setMinimum(0)
        self.ui.horizontalSlider_2.setMaximum(100)
        self.ui.horizontalSlider_2.setSingleStep(1)
        self.ui.label_13.setText(str(kd))
        self.ui.horizontalSlider_2.valueChanged.connect(self.valueChange_2)

        self.ui.horizontalSlider_3.setMinimum(-40)
        self.ui.horizontalSlider_3.setMaximum(40)
        self.ui.horizontalSlider_3.setSingleStep(1)
        self.ui.label_14.setText(str(offset_pixel_y))
        self.ui.horizontalSlider_3.valueChanged.connect(self.valueChange_3)

        self.ui.horizontalSlider_3.setMinimum(0)
        self.ui.horizontalSlider_3.setMaximum(100)
        self.ui.horizontalSlider_3.setSingleStep(1)
        self.ui.label_14.setText(str(kp))
        self.ui.horizontalSlider_3.valueChanged.connect(self.valueChange_4)


        self.ui.checkBox.stateChanged.connect(self.boxChange_1)
        self.ui.checkBox_2.stateChanged.connect(self.boxChange_2)
        self.ui.checkBox_3.stateChanged.connect(self.boxChange_3)

        self.ui.pushButton_3.clicked.connect(self.outButton)


    def valueChange_4(self):
        global kp
        kp = round(self.ui.horizontalSlider_4.value() / 10, 1)
        self.ui.label_12.setText(str(mouses_offset_ratio))
    def valueChange_1(self):
        global ki
        ki = round(self.ui.horizontalSlider.value() / 10, 1)
        self.ui.label_12.setText(str(mouses_offset_ratio))

    def valueChange_2(self):
        global kd
        kd = self.ui.horizontalSlider_2.value()
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

    # 程序退出
    def outButton(self):
        global out_check
        winsound.Beep(600, 200)
        out_check = 1
        self.close()
