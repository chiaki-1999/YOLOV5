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
    device = select_device('')
    model = DetectMultiBackend(weights, device=device, dnn=False, data=data, fp16=True)
    model.warmup(imgsz=(1, 3, *[img_size, img_size]))  # warmup
    return model


def interface_img(img, model):
    stride, names = model.stride, model.names

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
                line = (names[int(cls)], *xywh, int(100 * conf))
                if 0.1 < (xywh[2] / xywh[3]) < 0.9 and xywh[3] < 0.8:
                    box_list.append(line)
    return box_list


def draw_box(img, box_lists):
    img_h, img_w, _ = img.shape
    i = 0
    for _box in box_lists:
        i += 1
        x1 = int(_box[1] * img_w - _box[3] * img_w / 2)
        y1 = int(_box[2] * img_h - _box[4] * img_h / 2)
        x2 = int(x1 + _box[3] * img_w)
        y2 = int(y1 + _box[4] * img_h)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img, (str(i) + _box[0]), (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255))
    return img


FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
info_dir = os.path.join(ROOT, 'information.csv')

conf_thres = 0.3
iou_thres = 0.4
max_det = 1000

with open(info_dir, 'r', encoding='utf-8', newline='') as fr:
    reader = csv.DictReader(fr)
    for r in reader:
        pass
    weights = r['pth_dir']
    data = r['yaml_dir']
fr.close()
