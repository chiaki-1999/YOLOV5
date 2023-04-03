from math import *
from simple_pid import PID
from grab_screen import get_inspection_size

pid_x = PID(1.2, 8, 0.03, setpoint=0, sample_time=0.001, )
pid_y = PID(1.22, 3, 0.001, setpoint=0, sample_time=0.001, )
pid_x.output_limits = (-4000 , 4000)
pid_y.output_limits = (-3000 , 3000)

top_x, top_y, len_x, len_y = get_inspection_size()
mouse = pynput.mouse.Controller()
DETECT_ARRANGE = 8000
k = 4.07
def lock(aims):
    mouse_pos_x, mouse_pos_y = mouse.position
    aims_copy = [(tag, x_c, y_c, width, height) for tag, x_c, y_c, width, height in aims
                 if (len_x * float(x_c) + top_x - mouse_pos_x) ** 2 + (len_y * float(y_c) + top_y - mouse_pos_y) ** 2 < DETECT_ARRANGE]
    if len(aims_copy):
        dist_list = []
        for det in aims_copy:
            _, x_c, y_c, _, _ = det
            dist = (len_x * float(x_c) + top_x - mouse_pos_x) ** 2 + (len_y * float(y_c) + top_y - mouse_pos_y) ** 2
            dist_list.append(dist)

        if dist_list:
            det = aims_copy[dist_list.index(min(dist_list))]
            tag, x_center, y_center, width, height = det
            x_center, width = len_x * float(x_center) + top_x, len_x * float(width)
            y_center, height = len_y * float(y_center) + top_y, len_y * float(height)
            rel_x = int(k * atan((mouse_pos_x - x_center) / 640) * 640)
            rel_y = int(k * atan((mouse_pos_y - y_center + 1 / 8 * height) / 640) * 640)  # 瞄準高度可自行調整(建議為1/4)
            pid_move_x = pid_x(rel_x)
            pid_move_y = pid_y(rel_y)
            return round(pid_move_x), round(pid_move_y)