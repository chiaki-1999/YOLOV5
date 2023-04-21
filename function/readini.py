import csv
import os
import sys
from pathlib import Path

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
info_dir = os.path.join(ROOT, 'information.csv')
with open(info_dir, 'r', encoding='utf-8', newline='') as fr:
    reader = csv.DictReader(fr)
    r = next(reader)
    show_monitor = r['show_monitor']
    screen_size = r['screen_size']
    screen_info = r['screen_info'].replace('(', ',').replace(')', ',').replace(' ', '').split(',')
    screen_info = tuple(map(int, screen_info[3:6]))
    weights = r['pth_dir']
    data = r['yaml_dir']

screen_size = screen_size.split('*')
grab_size = 416
screen_width, screen_height = (int(screen_size[0]), int(screen_size[1]))
grab = (int((screen_width - grab_size) / 2), int((screen_height - grab_size) / 2), grab_size, grab_size)
pos_center = (int(screen_width / 2), int(screen_height / 2))


def get_show_monitor():
    return show_monitor
