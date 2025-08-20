import cv2
import numpy as np
from PIL import Image

from camera import Fusion

front = cv2.imread("./imgs/aerial_view/new_front.jpg")
back = cv2.imread("./imgs/aerial_view/new_back.jpg")
left = cv2.imread("./imgs/aerial_view/new_left.jpg")
right = cv2.imread("./imgs/aerial_view/new_right.jpg")
imgs = [front, back, left, right]

fusion = Fusion(imgs, r"D:\Projects\Work\06_dahua_surround\cfgs\surround.yaml")
weight, mask = fusion.get_weights_and_masks()

Image.fromarray((weight * 255).astype(np.uint8)).save("weights.png")
Image.fromarray(mask.astype(np.uint8)).save("masks.png")