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


def load_model():
    global weights
    model_trt = TRTModule()
    model_trt.load_state_dict(torch.load(weights))
    device = select_device('cuda:0')
    model_trt = model_trt.to(device)
    model_trt.half()
    return model_trt


def interface_img(img, model):
    stride, names = model.stride, model.names
    h, w = img.shape[:2]
    img = cv2.resize(img, (w, h), interpolation=cv2.INTER_LINEAR)
    im = letterbox(img, 416, stride=stride, auto=True)[0]
    im = im.transpose((2, 0, 1))[::-1]
    im = np.ascontiguousarray(im)
    im = torch.tensor(im).to(model.device, dtype=torch.float16)
    if len(im.shape) == 3:
        im = im.unsqueeze(0)
    with torch.no_grad():
        pred = model(im, augment=False, visualize=False)
        pred = pred.float()
        pred = non_max_suppression(pred, conf_thres, iou_thres, max_det=max_det)

    box_list = []
    for i, det in enumerate(pred):
        gn = torch.tensor(img.shape)[[1, 0, 1, 0]]
        if len(det):
            det[:, :4] = scale_boxes(im.shape[2:], det[:, :4], img.shape).round()
            for *xyxy, conf, cls in reversed(det):
                xywh = ((torch.tensor(xyxy).float() + 0.5).int() / gn).tolist()
                line = (names[int(cls)], *xywh)
                if 0.1 < (xywh[2] / xywh[3]) < 0.9 and xywh[3] < 0.8:
                    box_list.append(line)
    return box_list


FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
info_dir = os.path.join(ROOT, 'information.csv')

conf_thres = 0.5
iou_thres = 0.5
max_det = 1000

with open(info_dir, 'r', encoding='utf-8', newline='') as fr:
    reader = csv.DictReader(fr)
    for r in reader:
        pass
    weights = r['pth_dir']
    data = r['yaml_dir']
fr.close()
