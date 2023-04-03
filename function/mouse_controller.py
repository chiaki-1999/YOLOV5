import csv
import os
import sys
from pathlib import Path
from threading import Thread

import winsound
from PyQt5.QtWidgets import QApplication, QMainWindow
from pynput import mouse
from lock import lock
from ShowUI import Ui_MainWindow
from function.grab_screen import get_screen_scale
from function.mouse.mouse import Mouse

mouse_left_click = False
mouse_right_click = False
mouses_offset_ratio = 0.0
flag_lock_obj_left = False
flag_lock_obj_right = False
offset_pixel_center = 0
offset_pixel_y = 0
out_check = 0

class ShowWindows(QMainWindow):

    def __init__(self):
        global mouses_offset_ratio, offset_pixel_center, offset_pixel_y
        super(ShowWindows, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.horizontalSlider.setMinimum(0)
        self.ui.horizontalSlider.setMaximum(20)
        self.ui.horizontalSlider.setSingleStep(1)
        self.ui.label_12.setText(str(mouses_offset_ratio))
        self.ui.horizontalSlider.valueChanged.connect(self.valueChange_1)

        self.ui.horizontalSlider_2.setMinimum(0)
        self.ui.horizontalSlider_2.setMaximum(10)
        self.ui.horizontalSlider_2.setSingleStep(1)
        self.ui.label_13.setText(str(offset_pixel_center))
        self.ui.horizontalSlider_2.valueChanged.connect(self.valueChange_2)

        self.ui.horizontalSlider_3.setMinimum(-20)
        self.ui.horizontalSlider_3.setMaximum(20)
        self.ui.horizontalSlider_3.setSingleStep(1)
        self.ui.label_14.setText(str(offset_pixel_y))
        self.ui.horizontalSlider_3.valueChanged.connect(self.valueChange_3)

        self.ui.checkBox.stateChanged.connect(self.boxChange_1)
        self.ui.checkBox_2.stateChanged.connect(self.boxChange_2)

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
        offset_pixel_y = self.ui.horizontalSlider_3.value()
        self.ui.label_14.setText(str(offset_pixel_y))

    def boxChange_1(self):
        global flag_lock_obj_left
        flag_lock_obj_left = self.ui.checkBox.isChecked() or self.ui.checkBox_2.isChecked()
        if flag_lock_obj_left:
            self.ui.label_2.setText('启动状态（Open）')
        else:
            self.ui.label_2.setText('启动状态（Close）')
        winsound.Beep(600, 200)

    def boxChange_2(self):
        global flag_lock_obj_right
        flag_lock_obj_right = self.ui.checkBox.isChecked() or self.ui.checkBox_2.isChecked()
        if flag_lock_obj_right:
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
        sys.exit(0)


def track_target_ratio(box_lists):
    pos_min = (0, 0)
    if len(box_lists) != 0:
        dis_min = max_pos
        for _box in box_lists:
            x_target = int(_box[1] * grab_width + grab_x)
            y_target = int(_box[2] * grab_height + grab_y)
            if (x_target - pos_center[0]) ** 2 + (y_target - pos_center[1]) < dis_min ** 2:
                dis_min = (x_target - pos_center[0]) ** 2 + (y_target - pos_center[1])
                pos_min = (x_target - pos_center[0], y_target - pos_center[1])
        return pos_min[0], pos_min[1], 1
    else:
        return 0, 0, 0


def show_ui():
    app = QApplication([])
    windows = ShowWindows()
    windows.show()
    app.exec_()


def on_click(x, y, button, pressed):
    global mouse_left_click, mouse_right_click
    if button == mouse.Button.left:
        mouse_left_click = pressed
    elif button == mouse.Button.right:
        mouse_right_click = pressed

def usb_control(usb, kill):
    global mouse_left_click, mouse_right_click, mouses_offset_ratio, offset_pixel_center, offset_pixel_y, out_check, flag_lock_obj_left, flag_lock_obj_right
    ui_show = Thread(target=show_ui)
    ui_show.start()

    listener_mouse = mouse.Listener(on_click=on_click)
    listener_mouse.start()

    while True:
        kill.value = out_check
        if usb.empty() is True:
            continue
        box_lists = usb.get()
        if ((mouse_left_click and flag_lock_obj_left)
                or (mouse_right_click and flag_lock_obj_right)):
            coordinate = lock(box_lists)
            if bool(coordinate):
                M_X1, M_Y1 = coordinate
                print(" M_X1 : ", M_X1, " M_Y1 : ", M_Y1)
                Mouse.mouse.move(M_X1, M_Y1)
