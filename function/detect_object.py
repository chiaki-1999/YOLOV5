import csv
import os
import sys
from pathlib import Path

import numpy as np
import torch

from models.common import DetectMultiBackend
from utils.augmentations import (letterbox)
from utils.general import (Profile, cv2,
                           non_max_suppression, scale_boxes, xyxy2xywh)
from utils.torch_utils import select_device


def load_model(img_size):
    device = select_device('cuda:0')
    model = DetectMultiBackend(weights, device=device, dnn=False, data=data, fp16=True)
    model.warmup(imgsz=(1, 3, *[img_size, img_size]))  # warmup
    return model


def parse_array(arr):
    new_arr = []
    for row in arr:
        new_row = [float(val) if '.' in val else int(val) for val in row]
        new_arr.append(new_row)
    return new_arr


def interface_img(img, model):
    stride, names = model.stride, model.names
    h, w = img.shape[:2]
    img = cv2.resize(img, (int(w * 0.8), int(h * 0.8)), interpolation=cv2.INTER_LINEAR)

    im = letterbox(img, 640, stride=stride, auto=True)[0]
    im = im.transpose((2, 0, 1))[::-1]
    im = np.ascontiguousarray(im)

    dt = (Profile(), Profile(), Profile())
    with dt[0]:
        im = torch.from_numpy(im).to(model.device)
        im = im.half() if model.fp16 else im.float()
        im /= 255
        if len(im.shape) == 3:
            im = im[None]

    with dt[1]:
        pred = model(im, augment=False, visualize=False)

    with dt[2]:
        pred = non_max_suppression(pred, conf_thres, iou_thres, max_det=max_det)

    box_list = []
    for i, det in enumerate(pred):
        gn = torch.tensor(img.shape)[[1, 0, 1, 0]]
        if len(det):
            det[:, :4] = scale_boxes(im.shape[2:], det[:, :4], img.shape).round()
            for *xyxy, conf, cls in reversed(det):
                xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()
                line = (cls, *xywh)
                line = ('%g ' * len(line)).rstrip() % line
                line = line.split(' ')
                if 0.1 < (xywh[2] / xywh[3]) < 0.9 and xywh[3] < 0.8:
                    box_list.append(line)
    if bool(box_list):
        box_list = parse_array(box_list)

    return box_list


FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
info_dir = os.path.join(ROOT, 'information.csv')

conf_thres = 0.5
iou_thres = 0.4
max_det = 800

with open(info_dir, 'r', encoding='utf-8', newline='') as fr:
    reader = csv.DictReader(fr)
    for r in reader:
        pass
    weights = r['pth_dir']
    data = r['yaml_dir']
fr.close()
