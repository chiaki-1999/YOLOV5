from pynput import mouse

from function.readini import grab_height, grab_x, grab_width, grab_y, pos_center
from util import HFOV, VFOV


def track_target_ratio(target_box, offset_ratio, mouses_offset_ratio):
    offset = int(target_box[4] * grab_height * offset_ratio)
    x = (int(target_box[1] * grab_width + grab_x) - pos_center[0]) * mouses_offset_ratio
    y = (int(target_box[2] * grab_height + grab_y) - pos_center[1] - offset) * mouses_offset_ratio
    return HFOV(x), VFOV(y), 1
