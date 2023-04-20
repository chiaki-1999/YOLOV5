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


def mouse_listener():
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()


def track_target_ratio(target_box, offset_ratio, mouses_offset_ratio):
    offset = int(target_box[4] * grab_height * offset_ratio)
    x = (int(target_box[1] * grab_width + grab_x) - pos_center[0]) * mouses_offset_ratio
    y = (int(target_box[2] * grab_height + grab_y) - pos_center[1] - offset) * mouses_offset_ratio
    return HFOV(x), VFOV(y), 1


def usb_control(serialized_data):
    box_list, flag_lock_obj_left, flag_lock_obj_right, mouses_offset_ratio, offset_pixel_y, conf = serialized_data
    pos_min_x, pos_min_y, has_target = track_target_ratio(box_list, offset_pixel_y, mouses_offset_ratio)
    if mouse_left_click and flag_lock_obj_left or mouse_right_click and flag_lock_obj_right and has_target:
        move_to_position(int(pos_min_x), int(pos_min_y), conf)
    print("计算坐标: {:.2f} ms".format((time.time() - zb) * 1000))


def move_to_position(pos_x, pos_y, pixel=5):
    # 计算需要移动的段数
    segment = pos_x / pixel
    # 根据需要移动的段数调整像素值
    for threshold in [20, 15, 10, 5]:
        if segment > threshold:
            pixel = pixel * 2
            segment = pos_x / pixel
    # 计算需要迭代的次数
    abs_segment = abs(segment)
    # 确定每个段的方向
    symbol = math.copysign(1, segment)
    # 循环移动鼠标
    for i in range(abs_segment):
        # 移动鼠标到下一个位置
        Mouse.mouse.move(symbol * pixel, pos_y)
        # 控制每个步骤之间的时间间隔，让鼠标移动更平滑
        time.sleep(random.uniform(0.001, 0.002))




