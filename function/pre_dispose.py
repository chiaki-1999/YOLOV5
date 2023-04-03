import csv
import multiprocessing
import os
import sys
import time
from multiprocessing import set_start_method, Queue, Process
from pathlib import Path
import cv2
import numpy as np

from function.detect_object import load_model, interface_img
from function.grab_screen import win32_capture
from function.mouse_controller import usb_control
from util import milli_sleep

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
info_dir = os.path.join(ROOT, 'information.csv')


def draw_box(img, box_list):
    if len(box_list) == 0:
        return img

    gs = screen_info[2]
    gy = screen_info[2]

    for _box in box_list:
        x_center = _box[1] * gs
        y_center = _box[2] * gy
        w = _box[3] * gs
        h = _box[4] * gy
        x1, y1 = int(x_center - w / 2), int(y_center - h / 2)
        x2, y2 = int(x_center + w / 2), int(y_center + h / 2)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img, f'{_box[0]}', (x1 + 5, y1 + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        return img


def draw_fps(img, fps_time, fps_list):
    timer = time.time() - fps_time
    if len(fps_list) > 10:
        fps_list.pop(0)
        fps_list.append(timer)
    else:
        fps_list.append(timer)
    cv2.putText(img, "lock:{:.1f}".format(int(1 / np.mean(fps_list))), (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                (0, 0, 255), 2)

    cv2.putText(img, "FPS:{:.1f}".format(1. / (time.time() - fps_time)), (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1,
                (27, 0, 221), 2)
    return img


def lock_target(usb, kill):
    fps_list = []
    model = load_model(img_size=640)
    grab_info = screen_info
    while True:
        if kill.value == 1:
            break
        fps_time = time.time()
        img = win32_capture(grab_info=grab_info)
        milli_sleep(3)
        box_list = interface_img(img, model)

        usb.put(box_list)

        if show_monitor == '开启':
            img = draw_box(img, box_list)
            img = draw_fps(img, fps_time, fps_list)

            cv2.namedWindow('game_plug_in', cv2.WINDOW_KEEPRATIO)
            cv2.imshow('game_plug_in', img)
            cv2.waitKey(1)
            box_list.clear()


def main():
    set_start_method('spawn')
    q = Queue()
    kill = multiprocessing.Value('i')
    lock = Process(target=lock_target, args=(q, kill))
    usb = Process(target=usb_control, args=(q, kill))
    lock.start()
    usb.start()


with open(info_dir, 'r', encoding='utf-8', newline='') as fr:
    reader = csv.DictReader(fr)
    for r in reader:
        pass

    show_monitor = r['show_monitor']
    screen_info = (r['screen_info'])

    screen_info = screen_info.replace('(', ',')
    screen_info = screen_info.replace(')', ',')
    screen_info = screen_info.replace(' ', '')
    screen_info = screen_info.split(',')
    screen_info = int(screen_info[3]), int(screen_info[4]), int(screen_info[5])
