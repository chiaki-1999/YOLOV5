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

screen_size = screen_size.split('*')
screen_size = (int(screen_size[0]), int(screen_size[1]))


def get_show_monitor():
    return show_monitor
