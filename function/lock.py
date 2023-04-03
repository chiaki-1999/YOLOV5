from math import *
from simple_pid import PID
from grab_screen import get_inspection_size

pid_x = PID(1.2, 8, 0.03, setpoint=0, sample_time=0.001, )
pid_y = PID(1.22, 3, 0.001, setpoint=0, sample_time=0.001, )
pid_x.output_limits = (-4000 , 4000)
pid_y.output_limits = (-3000 , 3000)
TOP_X, TOP_Y, LEN_X, LEN_Y = get_inspection_size()
MOUSE = pynput.mouse.Controller()
DETECT_RANGE = 8000
K = 4.07

def lock(aims):
    mouse_pos_x, mouse_pos_y = MOUSE.position
    aims_copy = [(tag, x_c, y_c, width, height) for tag, x_c, y_c, width, height in aims
                 if (LEN_X * float(x_c) + TOP_X - mouse_pos_x) ** 2 + (LEN_Y * float(y_c) + TOP_Y - mouse_pos_y) ** 2 < DETECT_RANGE]
    if not aims_copy:
        return None
    dist_list = []
    for det in aims_copy:
        _, x_c, y_c, _, _ = det
        dist = (LEN_X * float(x_c) + TOP_X - mouse_pos_x) ** 2 + (LEN_Y * float(y_c) + TOP_Y - mouse_pos_y) ** 2
        dist_list.append(dist)

    det = aims_copy[dist_list.index(min(dist_list))]
    tag, x_center, y_center, width, height = det
    x_center, width = LEN_X * float(x_center) + TOP_X, LEN_X * float(width)
    y_center, height = LEN_Y * float(y_center) + TOP_Y, LEN_Y * float(height)
    rel_x, rel_y = calculate_relative_position(mouse_pos_x, mouse_pos_y, x_center, y_center, height)
    pid_move_x = pid_x(rel_x)
    pid_move_y = pid_y(rel_y)
    return round(pid_move_x), round(pid_move_y)


def calculate_relative_position(mouse_pos_x, mouse_pos_y, x_center, y_center, height):
    rel_x = int(K * math.atan((mouse_pos_x - x_center) / 640) * 640)
    rel_y = int(K * math.atan((mouse_pos_y - y_center + 1 / 8 * height) / 640) * 640)  # 瞄準高度可自行調整(建議為1/4)
    return rel_x, rel_y