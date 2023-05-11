import heapq
import math
import threading
import time
from multiprocessing import get_context, Process

import cv2
import numpy as np
import win32con
import win32gui
import winsound
from PyQt5.QtWidgets import QApplication, QMainWindow
from pynput import mouse

from SecondUI import Ui_MainWindow
from function.detect_object import load_model, interface_img
from function.grab_screen import win32_capture_Init
from function.mouse.mouse import Mouse
from function.readini import screen_info, get_show_monitor, pos_center, grab
from util import HOV_new, OVF_new

pos_center_w, pos_center_h = pos_center[0], pos_center[1]
grab_x, grab_y, grab_width, grab_height = grab
mouse_left_click, mouse_right_click = False, False
mouses_offset_ratio = 3  # 瞄准速度
offset_pixel_y = 0.25  # 瞄准百分比 0%是中心
out_check = 0  # 退出标识
flag_lock_obj_left = False
flag_lock_obj_right = False
auto_fire_switch = False
kp = 1
ki = 0
fire = False


def show_ui():
    app = QApplication([])
    windows = MainWindows()
    windows.show()
    app.exec_()


def mul_thr():
    t1 = threading.Thread(target=show_ui)
    t1.start()
    t1 = threading.Thread(target=auto_fire)
    t1.start()
    t3 = threading.Thread(target=lock_target)
    t3.start()


def run():
    Process(target=mul_thr, args=()).start()


show_monitor = get_show_monitor()


def lock_target():
    global show_monitor, out_check
    models = load_model(416)
    cp = win32_capture_Init()
    mouse_listener()
    while not out_check:
        fps_time = time.time()
        img = cp.capture()
        jt_time = time.time() - fps_time
        box_lists = interface_img(img, models)  # 这里使用 img
        tl_time = time.time() - jt_time
        if box_lists:
            usb_control(get_closest_target_index(box_lists), fps_time)
        yd_time = time.time() - tl_time
        print("截图时间： {:.2f} ms   推理时间： {:.2f} ms   移动时间： {:.2f} ms   循环时间推理时间： {:.2f} ms".format(
            jt_time * 1000, tl_time * 1000, yd_time * 1000  , (time.time() - fps_time) * 1000))
        if show_monitor == '开启':
            show_img(img, box_lists, fps_time)


def usb_control(box_list, dt):
    pos_min_x, pos_min_y, has_target = track_target_ratio(box_list, dt)
    if (mouse_left_click and flag_lock_obj_left) or (mouse_right_click and flag_lock_obj_right):
        if has_target:
            Mouse.mouse.move(int(pos_min_x * kp), int(pos_min_y * kp))


def track_target_ratio(target_box, dt):
    global fire
    x_dt = ((time.time() - dt) * 1000)
    offset = int(target_box[4] * grab_height * offset_pixel_y)
    x = HOV_new((int(target_box[1] * grab_width + grab_x) - pos_center_w))
    y = int(target_box[2] * grab_height + grab_y) - pos_center_h - offset
    abs_x, abs_y = abs(x), abs(y)
    # 移动补偿
    if abs_x >= 10:
        symbol = math.copysign(1, x)
        x_compensate = int((mouses_offset_ratio * x_dt) * symbol)
        x += x_compensate
    return x, y, abs_x <= 3 and abs_y <= 3

def get_closest_target_index(box_lists):
    body_boxes = [box_list for box_list in box_lists if 0 in box_list]
    if body_boxes:
        boxes = np.array(body_boxes)
    else:
        boxes = np.array(box_lists)
    centers = (boxes[:, 1:3] + boxes[:, 3:5]) / 2
    target_center = np.array([pos_center_w, pos_center_h])
    distances = np.sum(np.square(centers - target_center), axis=1)
    closest_index = np.argmin(distances)
    return body_boxes[closest_index] if body_boxes else box_lists[closest_index]



def auto_fire():
    global fire, auto_fire_switch
    while True:
        if fire and auto_fire_switch:
            Mouse.mouse.press(1)
            milli_sleep(random.uniform(0.03, 0.04))
            Mouse.mouse.release(1)
            milli_sleep(random.uniform(0.03, 0.05))
            fire = False


def on_click(x, y, button, pressed):
    global mouse_left_click, mouse_right_click
    if button == mouse.Button.left:
        mouse_left_click = pressed
    elif button == mouse.Button.right:
        mouse_right_click = pressed


def mouse_listener():
    listener_mouse = mouse.Listener(on_click=on_click)
    listener_mouse.start()






def show_img(img, box_lists, fps_time):
    img = draw_box(img, box_lists)
    img = draw_fps(img, fps_time, box_lists)
    cv2.imshow("game", img)
    hwnd = win32gui.FindWindow(None, "game")
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                          win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
    cv2.waitKey(1)


def draw_box(img, box_list):
    if not box_list:
        return img
    gs = screen_info[2]
    gy = screen_info[2]
    for box in box_list:
        x_center = box[1] * gs
        y_center = box[2] * gy
        w = box[3] * gs
        h = box[4] * gy
        x1, y1 = int(x_center - w / 2), int(y_center - h / 2)
        x2, y2 = int(x_center + w / 2), int(y_center + h / 2)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img, f'{box[0]}', (x1 + 5, y1 + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    return img


def draw_fps(img, fps_time, fps_list):
    if not fps_list:
        return img
    timer = time.time() - fps_time
    if len(fps_list) > 10:
        fps_list.pop(0)
    fps_list.append(timer)
    fps_list = [x for x in fps_list if isinstance(x, (int, float))]
    fps_list = list(fps_list)
    fps = len(fps_list) / sum(fps_list)
    fps_text = "FPS:{:.1f} lock:{:.1f}".format(fps, int(1 / np.mean(fps_list)))
    cv2.putText(img, fps_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    return img


class MainWindows(QMainWindow):

    def __init__(self):
        global mouses_offset_ratio, kp, offset_pixel_y, ki
        super(MainWindows, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.horizontalSlider.setMinimum(0)
        self.ui.horizontalSlider.setMaximum(60)
        self.ui.horizontalSlider.setSingleStep(1)
        self.ui.label_12.setText(str(mouses_offset_ratio))
        self.ui.horizontalSlider.valueChanged.connect(self.valueChange_1)

        self.ui.horizontalSlider_2.setMinimum(0)
        self.ui.horizontalSlider_2.setMaximum(10)
        self.ui.horizontalSlider_2.setSingleStep(1)
        self.ui.label_13.setText(str(kp))
        self.ui.horizontalSlider_2.valueChanged.connect(self.valueChange_2)

        self.ui.horizontalSlider_3.setMinimum(0)
        self.ui.horizontalSlider_3.setMaximum(50)
        self.ui.horizontalSlider_3.setSingleStep(1)
        self.ui.label_14.setText(str(offset_pixel_y))
        self.ui.horizontalSlider_3.valueChanged.connect(self.valueChange_3)

        self.ui.horizontalSlider_4.setMinimum(0)
        self.ui.horizontalSlider_4.setMaximum(0)
        self.ui.horizontalSlider_4.setSingleStep(1)
        self.ui.horizontalSlider_4.setValue(0)
        self.ui.label_19.setText(str(0))
        self.ui.horizontalSlider_4.valueChanged.connect(self.valueChange_4)

        self.ui.horizontalSlider_5.setMinimum(0)
        self.ui.horizontalSlider_5.setMaximum(100)
        self.ui.horizontalSlider_5.setSingleStep(1)
        self.ui.label_20.setText(str(ki))
        self.ui.horizontalSlider_5.valueChanged.connect(self.valueChange_5)

        self.ui.checkBox.stateChanged.connect(self.boxChange_1)
        self.ui.checkBox_2.stateChanged.connect(self.boxChange_2)
        self.ui.checkBox_3.stateChanged.connect(self.boxChange_3)

        self.ui.pushButton_3.clicked.connect(self.outPush)

    def valueChange_1(self):
        global mouses_offset_ratio
        mouses_offset_ratio = round(self.ui.horizontalSlider.value() / 10, 1)
        self.ui.label_12.setText(str(mouses_offset_ratio))

    def valueChange_2(self):
        global kp
        kp = round(self.ui.horizontalSlider_2.value() / 10, 1)
        self.ui.label_13.setText(str(kp))

    def valueChange_3(self):
        global offset_pixel_y
        offset_pixel_y = round(self.ui.horizontalSlider_3.value() / 100, 2)
        self.ui.label_14.setText(str(offset_pixel_y))

    def valueChange_4(self):
        self.ui.label_19.setText(str(0))

    def valueChange_5(self):
        global ki
        ki = round(self.ui.horizontalSlider_5.value() / 100, 2)
        self.ui.label_20.setText(str(ki))

    def boxChange(self):
        global flag_lock_obj_left, flag_lock_obj_right, auto_fire_switch
        if auto_fire_switch:
            self.ui.label_2.setText('使用PID')
        else:
            if flag_lock_obj_left:
                if flag_lock_obj_right:
                    self.ui.label_2.setText('启动状态（左或右）')
                else:
                    self.ui.label_2.setText('启动状态（左）')
            else:
                if flag_lock_obj_right:
                    self.ui.label_2.setText('启动状态（右）')
                else:
                    self.ui.label_2.setText('启动状态（关闭）')

    def boxChange_1(self):
        global flag_lock_obj_left
        flag_lock_obj_left = self.ui.checkBox.isChecked()
        self.boxChange()

    def boxChange_2(self):
        global flag_lock_obj_right
        flag_lock_obj_right = self.ui.checkBox_2.isChecked()
        self.boxChange()

    def boxChange_3(self):
        global auto_fire_switch
        auto_fire_switch = self.ui.checkBox_3.isChecked()
        self.boxChange()

    def outPush(self):
        global out_check
        winsound.Beep(600, 200)
        out_check = 1
        self.close()
