import time

import keyboard
import msgpack
from pynput import mouse

from function.mouse.mouse import Mouse
from function.readini import grab_height, grab_x, grab_width, grab_y, pos_center
from util import HFOV, VFOV

mouse_x, mouse_y = mouse.Controller().position
mouse_left_click = False
mouse_right_click = False
flag_lock_obj_both = False


def on_click(x, y, button, pressed):
    global mouse_left_click, mouse_right_click, flag_lock_obj_both
    if button == mouse.Button.left:
        mouse_left_click = pressed
    elif button == mouse.Button.right:
        mouse_right_click = pressed


listener_mouse = mouse.Listener(on_click=on_click)
listener_mouse.start()


def track_target_ratio(target_box, offset_ratio, mouses_offset_ratio):
    offset = int(target_box[4] * grab_height * offset_ratio)
    x = (int(target_box[1] * grab_width + grab_x) - pos_center[0]) * mouses_offset_ratio
    y = (int(target_box[2] * grab_height + grab_y) - pos_center[1] - offset) * mouses_offset_ratio
    return HFOV(x), VFOV(y), 1


def usb_control(usb):
    while True:
        if not usb.empty():
            zb = time.time()
            serialized_data = usb.get()
            box_list, out_check, flag_lock_obj_left, flag_lock_obj_right, mouses_offset_ratio, offset_pixel_y, \
                offset_pixel_center, conf = msgpack.loads(serialized_data)
            if out_check:
                break
            if not box_list:
                continue
            pos_min_x, pos_min_y, has_target = track_target_ratio(box_list, offset_pixel_y, mouses_offset_ratio)
            if mouse_left_click and flag_lock_obj_left or mouse_right_click and flag_lock_obj_right and has_target:
                Mouse.mouse.move(int(pos_min_x), int(pos_min_y))
            print("计算坐标: {:.2f} ms".format((time.time() - zb) * 1000))
