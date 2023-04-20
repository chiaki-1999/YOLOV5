import heapq
import threading
import time
from multiprocessing import Process, get_context

import cv2
import msgpack
import numpy as np
import win32con
import win32gui
import winsound
from PyQt5.QtWidgets import QApplication, QMainWindow
from SecondUI import Ui_MainWindow
from function.detect_object import load_model, interface_img
from function.grab_screen import win32_capture, win32_capture_Init
from function.mouse_controller import usb_control, mouse_listener
from function.readini import screen_info, get_show_monitor, grab_width, grab_x, pos_center, grab_y, grab_height

mouses_offset_ratio = 1.4
flag_lock_obj_both = False
flag_lock_obj_left = False
flag_lock_obj_right = False
offset_pixel_center = 1
offset_pixel_y = 0.3
out_check = 0
conf = 5


def show_ui():
    app = QApplication.instance() or QApplication([])
    windows = MainWindows()
    windows.show()
    app.exec_()


def run():
    ctx = get_context('spawn')
    queue = ctx.Queue()
    t1 = threading.Thread(target=show_ui)
    t1.start()

    t2 = threading.Thread(target=img_capture, args=(queue,))
    t2.start()

    t3 = threading.Thread(target=lock_target, args=(queue,))
    t3.start()


show_monitor = get_show_monitor()


def lock_target(conn):
    global show_monitor, out_check, flag_lock_obj_left, flag_lock_obj_right, mouses_offset_ratio, offset_pixel_y, conf
    mouse_listener()
    models = load_model(416)
    while not out_check:
        if not conn.empty():
            img = conn.get()
            fps_time = time.time()
            box_lists = interface_img(img, models)  # 这里使用 img
            if box_lists:
                target_box_lists = get_target_box_lists(box_lists)
                min_index = get_closest_target_index(target_box_lists)
                print(" 推理延迟 ： {:.2f} ms".format((time.time() - fps_time) * 1000))
                target_box_lists[min_index], flag_lock_obj_left, flag_lock_obj_right, mouses_offset_ratio, \
                    offset_pixel_y, conf = serialized_data
                usb_control(serialized_data)
                print(" 处理完成 ： {:.2f} ms".format((time.time() - fps_time) * 1000))
                if show_monitor == '开启':
                    show_img(img, box_lists, fps_time)
    conn.clear()


def get_target_box_lists(box_lists):
    body_boxes = [box_list for box_list in box_lists if 0 in box_list]
    return body_boxes if body_boxes else box_lists


def get_closest_target_index(target_box_lists):
    distances = [((int(box[1] * grab_width + grab_x) - pos_center[0]) ** 2 +
                  (int(box[2] * grab_height + grab_y) - pos_center[1]) ** 2, i)
                 for i, box in enumerate(target_box_lists)]
    return heapq.nsmallest(1, distances)[0][1]


def show_img(img, box_lists, fps_time):
        img = draw_box(img, box_lists)
        img = draw_fps(img, fps_time, box_lists)
        cv2.imshow("game", img)
        hwnd = win32gui.FindWindow(None, "game")
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        cv2.waitKey(1)


def img_capture(conn2):
    global out_check
    win32_capture_Init()
    while not out_check:
        if conn2.empty():
            t = time.time()
            img = win32_capture()
            conn2.put(img)
            print(f"截图延迟：{((time.time() - t) * 1000):.2f} ms")
    conn2.close()


def draw_box(img, box_list):
    if not box_list:
        return img

    gs = screen_info[2]
    gy = screen_info[2]
    for box in box_list:
        print("box", box)
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
        global mouses_offset_ratio, offset_pixel_center, offset_pixel_y, conf
        super(MainWindows, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.horizontalSlider.setMinimum(0)
        self.ui.horizontalSlider.setMaximum(200)
        self.ui.horizontalSlider.setSingleStep(1)
        self.ui.label_12.setText(str(mouses_offset_ratio))
        self.ui.horizontalSlider.valueChanged.connect(self.valueChange_1)

        self.ui.horizontalSlider_2.setMinimum(0)
        self.ui.horizontalSlider_2.setMaximum(10)
        self.ui.horizontalSlider_2.setSingleStep(1)
        self.ui.label_13.setText(str(offset_pixel_center))
        self.ui.horizontalSlider_2.valueChanged.connect(self.valueChange_2)

        self.ui.horizontalSlider_3.setMinimum(0)
        self.ui.horizontalSlider_3.setMaximum(40)
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
        self.ui.label_20.setText(str(conf))
        self.ui.horizontalSlider_5.valueChanged.connect(self.valueChange_5)

        self.ui.checkBox.stateChanged.connect(self.boxChange_1)
        self.ui.checkBox_2.stateChanged.connect(self.boxChange_2)
        self.ui.checkBox_3.stateChanged.connect(self.boxChange_3)

        self.ui.pushButton_3.clicked.connect(self.outPush)

    def valueChange_1(self):
        global mouses_offset_ratio
        mouses_offset_ratio = round(self.ui.horizontalSlider.value() / 100, 2)
        self.ui.label_12.setText(str(mouses_offset_ratio))

    def valueChange_2(self):
        global offset_pixel_center
        offset_pixel_center = round(self.ui.horizontalSlider_2.value() / 10, 1)
        self.ui.label_13.setText(str(offset_pixel_center))

    def valueChange_3(self):
        global offset_pixel_y
        offset_pixel_y = round(self.ui.horizontalSlider_3.value() / 100, 2)
        self.ui.label_14.setText(str(offset_pixel_y))

    def valueChange_4(self):
        self.ui.label_19.setText(str(0))

    def valueChange_5(self):
        global conf
        conf = round(self.ui.horizontalSlider_5.value())
        self.ui.label_20.setText(str(conf))

    def boxChange(self):
        global flag_lock_obj_left, flag_lock_obj_right, flag_lock_obj_both
        if flag_lock_obj_both:
            self.ui.label_2.setText('启动状态自动开火')
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
        global flag_lock_obj_both
        flag_lock_obj_both = self.ui.checkBox_3.isChecked()
        self.boxChange()

    def outPush(self):
        global out_check
        winsound.Beep(600, 200)
        out_check = 1
        self.close()
