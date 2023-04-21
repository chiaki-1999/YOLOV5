import heapq
import threading
import time
from multiprocessing import get_context, Process

import cv2
import msgpack
import numpy as np
import win32con
import win32gui
import winsound
from PyQt5.QtWidgets import QApplication, QMainWindow
from pynput import mouse
from util import PID
from SecondUI import Ui_MainWindow
from function.detect_object import load_model, interface_img
from function.grab_screen import win32_capture, win32_capture_Init
from function.mouse.mouse import Mouse
from function.readini import screen_info, get_show_monitor, pos_center ,grab

pos_center_w, pos_center_h = pos_center
grab_x, grab_y, grab_width, grab_height = grab
mouse_left_click, mouse_right_click = False, False
mouses_offset_ratio = 0.8 #瞄准速度
offset_pixel_y = 0.25    #瞄准百分比 0%是中心
out_check = 0   #退出标识
flag_lock_obj_both = False
flag_lock_obj_left = False
flag_lock_obj_right = False


kp = 1  #kp
ki = 0.01  #ki

def show_ui():
    app = QApplication([])
    windows = MainWindows()
    windows.show()
    app.exec_()


def mul_thr(queue, queue2):
    t1 = threading.Thread(target=show_ui)
    t1.start()
    print(" ui 启动")
    t2 = threading.Thread(target=img_capture, args=(queue,))
    t2.start()
    print("截图启动")
    t3 = threading.Thread(target=lock_target, args=(queue, queue2,))
    t3.start()
    print("推理启动..")
    t4 = threading.Thread(target=usb_control, args=(queue2,))
    t4.start()
    print("鼠标瞄准启动..")


def run():
    ctx = get_context('spawn')
    queue = ctx.Queue()
    queue2 = ctx.Queue()
    Process(target=mul_thr, args=(queue, queue2,)).start()


show_monitor = get_show_monitor()


def lock_target(conn, conn2):
    global show_monitor, out_check, flag_lock_obj_left, flag_lock_obj_right, mouses_offset_ratio, offset_pixel_y
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
                conn2.put(target_box_lists[min_index])
                if show_monitor == '开启':
                    show_img(img, box_lists, fps_time)


body_pid_x = PID(0, kp, ki, 0)


def usb_control(conn2):
    mouse_listener()
    while not out_check:
        if not conn2.empty():
            t = time.time()
            box_list = conn.get()
            box_list = msgpack.loads(box_list)
            pos_min_x, pos_min_y, has_target = track_target_ratio(box_list)
            if mouse_left_click and flag_lock_obj_left or mouse_right_click and flag_lock_obj_right and has_target:
                Mouse.mouse.move(int(pos_min_x), int(pos_min_y))
                print(" 处理完成 ： {:.2f} ms".format((time.time() - t) * 1000))


def track_target_ratio(target_box):
    offset = int(target_box[4] * grab_height * offset_pixel_y)
    x = HOV_new((int(target_box[1] * grab_width + grab_x) - pos_center_w) * mouses_offset_ratio)
    y = OVF_new((int(target_box[2] * grab_height + grab_y) - pos_center_h - offset) * mouses_offset_ratio)
    return body_pid_x.cmd_pid(x), y, 1


def on_click(x, y, button, pressed):
    global mouse_left_click, mouse_right_click
    if button == mouse.Button.left:
        mouse_left_click = pressed
    elif button == mouse.Button.right:
        mouse_right_click = pressed


def mouse_listener():
    listener_mouse = mouse.Listener(on_click=on_click)
    listener_mouse.start()


def get_target_box_lists(box_lists):
    body_boxes = [box_list for box_list in box_lists if 0 in box_list]
    return body_boxes if body_boxes else box_lists


def get_closest_target_index(target_box_lists):
    distances = [((int(box[1] * grab_width + grab_x) - pos_center_w) ** 2 +
                  (int(box[2] * grab_height + grab_y) - pos_center_h) ** 2, i)
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
    print("截图初始化完成..... ")
    while not out_check:
        if conn2.empty():
            img = win32_capture()
            conn2.put(img)
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
        global mouses_offset_ratio, kp, offset_pixel_y, ki
        super(MainWindows, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.horizontalSlider.setMinimum(0)
        self.ui.horizontalSlider.setMaximum(200)
        self.ui.horizontalSlider.setSingleStep(1)
        self.ui.label_12.setText(str(mouses_offset_ratio))
        self.ui.horizontalSlider.valueChanged.connect(self.valueChange_1)

        self.ui.horizontalSlider_2.setMinimum(0)
        self.ui.horizontalSlider_2.setMaximum(100)
        self.ui.horizontalSlider_2.setSingleStep(1)
        self.ui.label_13.setText(str(kp))
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
        self.ui.label_20.setText(str(ki))
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
