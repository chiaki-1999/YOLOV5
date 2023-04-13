import heapq
import math
import time

import msgpack
import numpy
from pynput import mouse

from function.mouse.mouse import Mouse
from function.readini import screen_size
from util import PIDController, VFOV, HFOV

grab_size = 416

screen_width, screen_height = screen_size
grab = (int((screen_size[0] - grab_size) / 2), int((screen_size[1] - grab_size) / 2), grab_size, grab_size)
grab_x, grab_y, grab_width, grab_height = grab
pos_center = (int(screen_width / 2), int(screen_height / 2))
max_pos = int(pow((pow(pos_center[0], 2) + pow(pos_center[1], 2)), 0.5))
mouse_x, mouse_y = pos_center
mouse_left_click = False
mouse_right_click = False
auto_fire = False

flag_lock_obj_left, flag_lock_obj_right = False, False
offset_pixel_center = 0.7
conf = 0.05
kd = 0
flag_lock_obj = False

pid = PIDController(offset_pixel_center, conf, kd)


def get_last_item(usb):
    last_item = None
    while not usb.empty():
        last_item = usb.get()
    return last_item


def on_click(x, y, button, pressed):
    global mouse_left_click, mouse_right_click, flag_lock_obj_left, flag_lock_obj_right, \
        flag_lock_obj
    if button == mouse.Button.left:
        mouse_left_click = pressed
        flag_lock_obj = flag_lock_obj_left

    elif button == mouse.Button.right:
        mouse_right_click = pressed
        flag_lock_obj = flag_lock_obj_right

    if flag_lock_obj and not pressed:
        pid.reset()


def track_target_ratio(box_lists, offset_ratio):
    global auto_fire
    if not box_lists:
        return 0, 0, 0
    pid.update_pid(offset_pixel_center, conf, kd)
    distances = [((int(box[1] * grab_width + grab_x) - pos_center[0]) ** 2 +
                  (int(box[2] * grab_height + grab_y) - pos_center[1]) ** 2, i)
                 for i, box in enumerate(box_lists)]
    min_dist, min_index = heapq.nsmallest(1, distances)[0]
    target_box = box_lists[min_index]
    offset = int(target_box[4] * grab_height * offset_ratio)
    x = HFOV(int(target_box[1] * grab_width + grab_x) - pos_center[0])
    print(" x ", x)
    pid_x = pid.compute(x, 0, 0.01)
    print(" pid_x ", x)
    y = VFOV(int(target_box[2] * grab_height + grab_y) - pos_center[1] - offset)
    print(" min_dist ", min_dist," 当前值 " ,(max(grab_width, grab_height) / 2) ** 2)
    auto_fire = math.isclose(min_dist, (max(grab_width, grab_height) / 2) ** 2, rel_tol=0.08)
    print(" auto_fire ", auto_fire)
    print(" KP ", offset_pixel_center, "kd", conf)
    return pid_x, y, 1


def usb_control(usb):
    global flag_lock_obj_left, flag_lock_obj_right, offset_pixel_center, conf, auto_fire
    listener_mouse = mouse.Listener(on_click=on_click)
    listener_mouse.start()
    while True:
        zb = time.time()
        if usb.empty() is True:
            continue
        time.sleep(0.003)
        serialized_data = get_last_item(usb)
        dicts = msgpack.loads(serialized_data)
        box_list, out_check, flag_lock_obj_left, flag_lock_obj_right, mouses_offset_ratio, offset_pixel_y, \
            offset_pixel_center, conf, flag_lock_obj_both = dicts
        if not box_list:
            continue
        if out_check:
            break
        print(" box_list ", box_list)
        pos_min_x, pos_min_y, has_target = track_target_ratio(box_list, offset_pixel_y)
        if ((mouse_left_click and flag_lock_obj_left)
            or (mouse_right_click and flag_lock_obj_right)) \
                and has_target:
            Mouse.mouse.move(int(pos_min_x * mouses_offset_ratio), int(pos_min_y * mouses_offset_ratio))
            if flag_lock_obj_both and auto_fire:
                time.sleep(numpy.random.uniform(0.008, 0.012))
                Mouse.mouse.click(1)
        print("计算坐标: {:.2f} ms".format((time.time() - zb) * 1000))
