import cv2
import numpy as np
import torch

from function.readini import weights, data
from models.common import DetectMultiBackend
from utils.augmentations import (letterbox)
from utils.general import (non_max_suppression, scale_boxes, xyxy2xywh)
from utils.torch_utils import select_device


def load_model(img_size):
    device = select_device('')
    model = DetectMultiBackend(weights, device=device, dnn=False, data=data, fp16=True)
    model.warmup(imgsz=(1, 3, *[img_size, img_size]))  # warmup
    return model


def interface_img(img, models):
    if img is None:
        return None

    h, w = img.shape[:2]
    img = cv2.resize(img, (w, h), interpolation=cv2.INTER_LINEAR)

    im = letterbox(img, 416, stride=models.stride, auto=True)[0]
    im = im.transpose((2, 0, 1))[::-1]
    im = np.ascontiguousarray(im)

    im = torch.from_numpy(im).to(models.device)
    im = im.half() if models.fp16 else im.float()
    im = im.div(255.0).clamp(0.0, 1.0)  # 使用 .div() 方法进行除法操作，并使用 .clamp() 方法限制数据范围在 [0, 1] 之间
    if len(im.shape) == 3:
        im = im[None]

    with torch.no_grad():
        pred = models(im, augment=False, visualize=False)
        pred = non_max_suppression(pred, conf_thres, iou_thres, max_det=max_det)

    box_lists = []
    for i, det in enumerate(pred):
        gn = torch.tensor(img.shape)[[1, 0, 1, 0]]
        if len(det):
            det[:, :4] = scale_boxes(im.shape[2:], det[:, :4], img.shape).round()
            for *xyxy, conf, cls in reversed(det):
                xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()
                line = (models.names[int(cls)], *xywh)
                if 0.1 < (xywh[2] / xywh[3]) < 0.9 and xywh[3] < 0.8:
                    box_lists.append(line)

    return box_lists


conf_thres = 0.45
iou_thres = 0.45
max_det = 1000
