import csv
import os
from pathlib import Path
from sys import platform, path

import win32api
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from win32con import PROCESS_ALL_ACCESS
from win32process import SetPriorityClass, ABOVE_NORMAL_PRIORITY_CLASS

import function.pre_dispose
from SetUI import Ui_MainWindow
from function.grab_screen import get_screen_size
from util import set_dpi, is_admin, milli_sleep

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
if str(ROOT) not in path:
    path.append(str(ROOT))
info_dir = os.path.join(ROOT, 'function', 'information.csv')

screen_W = get_screen_size()["width"]
screen_H = get_screen_size()["height"]


def get_grab_info(screen=0, multi=1.0, gs=640):
    monitor_dev = win32api.EnumDisplayMonitors(None, None)
    x1 = monitor_dev[screen][2][0]
    y1 = monitor_dev[screen][2][1]
    x2 = monitor_dev[screen][2][2]
    y2 = monitor_dev[screen][2][3]

    w = int((x2 - x1) * multi)
    h = int((y2 - y1) * multi)

    gx = int(x1 + (w - gs) / 2)
    gy = int(y1 + (h - gs) / 2)

    gs = int((gs * h) / screen_H)

    return w, h, gx, gy, gs


class MainWindows(QMainWindow):
    def __init__(self):
        super(MainWindows, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.bind()

    def bind(self):
        self.ui.pushButton.clicked.connect(self.pth_push)
        self.ui.pushButton_2.clicked.connect(self.yaml_push)
        self.ui.pushButton_3.clicked.connect(self.check_push)
        self.ui.pushButton_4.clicked.connect(self.run_push)
        self.ui.progressBar.setRange(0, 100)
        self.ui.progressBar.setValue(0)

    def run_push(self):
        function.pre_dispose.main()
        for i in range(1, 101):
            milli_sleep(300)
            self.ui.progressBar.setValue(i)
        self.close()
        exit(1)

    def pth_push(self):
        choice = QFileDialog.getOpenFileName(MainWindows(), "选择权重文件")[0]
        self.ui.label_7.setText(choice)

    def yaml_push(self):
        choice = QFileDialog.getOpenFileName(MainWindows(), "选择配置文件")[0]
        self.ui.label_8.setText(choice)

    def check_push(self):
        self.ui.progressBar.setValue(0)
        screen_num = int(self.ui.comboBox.currentText())
        screen_multi = float(self.ui.comboBox_2.currentText())
        screen_info = get_grab_info(screen_num, screen_multi)
        screen_size = (str(screen_info[0]) + '*' + str(screen_info[1]))
        self.ui.label_10.setText(str(screen_size))
        pth_dir = self.ui.label_7.text()
        yaml_dir = self.ui.label_8.text()
        monitor = '开启' if self.ui.checkBox_2.isChecked() else '关闭'

        info = (f'屏幕编号：{screen_num} \t 屏幕倍率：{screen_multi}\t 屏幕分辨率：{screen_size}\n'
                f'权重路径：{pth_dir}\n'
                f'配置路径：{yaml_dir}\n'
                f'窗口显示状态：{monitor}')

        self.ui.label_9.setText(info)

        header = ['screen_num', 'screen_multi', 'screen_info', 'screen_size', 'pth_dir', 'yaml_dir', 'show_monitor']
        data = [[screen_num, screen_multi, screen_info, screen_size, pth_dir, yaml_dir, monitor]]

        with open(info_dir, 'w', encoding='utf-8', newline='') as fp:
            writer = csv.writer(fp)
            writer.writerow(header)
            writer.writerows(data)
        fp.close()

        for i in range(1, 101):
            milli_sleep(5)
            self.ui.progressBar.setValue(i)


if __name__ == '__main__':
    if not is_admin():  # 检查管理员权限
        print("=======请管理员身份运行此程序=======")
        exit()
    set_dpi()  # 设置高DPI不受影响
    # 提升进程优先级
    if platform == 'win32':
        pid = win32api.GetCurrentProcessId()
        handle = win32api.OpenProcess(PROCESS_ALL_ACCESS, True, pid)
        SetPriorityClass(handle, ABOVE_NORMAL_PRIORITY_CLASS)
    else:
        os.nice(1)
    app = QApplication([])
    windows = MainWindows()
    windows.show()
    app.exec_()
