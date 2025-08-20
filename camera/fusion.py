import cv2
import numpy as np
import yaml
from .utils import *

class Fusion:
    def __init__(self, images, cfg_path):
        # 四个视角画面
        self.images = images
        # 重叠区域掩膜
        self.masks = None
        # 融合权重
        self.weights = None

        with open(cfg_path, 'r') as f:
            cfg = yaml.safe_load(f)

        board_w = cfg['board']['width']
        board_h = cfg['board']['height']
        machine_w = cfg['machine']['width']
        machine_h = cfg['machine']['height']
        inner_w = cfg['inner']['width']
        inner_h = cfg['inner']['height']
        shift_w = cfg['shift']['width']
        shift_h = cfg['shift']['height']

        # 载体所占矩形区域范围
        # self.x_left = shift_w + board_w + inner_w
        # self.x_right = shift_w + board_w + inner_w + machine_w
        # self.y_top = shift_h + board_h + inner_h
        # self.y_bottom = shift_h + board_h + inner_h + machine_h
        self.x_left = 400
        self.x_right = 800
        self.y_top = 400
        self.y_bottom = 800

        self.machine_range = [self.x_left, self.x_right, self.y_top, self.y_bottom]

    def get_mask(self, img):
        """
        将重叠区域画面转为灰度，并二值化
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY)
        return mask

    def get_overlap_region_mask(self, imA, imB):
        """
        获取两个图片的重叠区域掩膜
        """
        overlap = cv2.bitwise_and(imA, imB)  # 按位与操作找到重叠区域
        mask = self.get_mask(overlap)  # 转换为二值掩码
        mask = cv2.dilate(mask, np.ones((2, 2), np.uint8), iterations=2)  # 形态学膨胀去噪
        return mask

    def get_outmost_polygon_boundary(self, img):
        """
        Given a mask image with the mask describes the overlapping region of
        two images, get the outmost contour of this region.
        """
        mask = self.get_mask(img)
        mask = cv2.dilate(mask, np.ones((2, 2), np.uint8), iterations=2)
        cnts, hierarchy = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,  # 只检测最外层轮廓
            cv2.CHAIN_APPROX_SIMPLE)[-2:]  # 压缩水平、垂直、对角方向的点，减少点数量

        # 获取面积最大的轮廓
        C = sorted(cnts, key=lambda x: cv2.contourArea(x), reverse=True)[0]

        # 多边形逼近
        polygon = cv2.approxPolyDP(C, 0.009 * cv2.arcLength(C, True), True)

        return polygon

    def get_weight_mask_matrix(self, imA, imB, dist_threshold=5):
        """
        计算重叠区域掩膜，和融合权重
        :param imA:
        :param imB:
        :param dist_threshold:
        :return:
        """
        # 步骤1: 检测重叠区域
        overlapMask = self.get_overlap_region_mask(imA, imB)  # 重叠区域掩膜
        overlapMaskInv = cv2.bitwise_not(overlapMask)  # 非重叠区域掩膜
        indices = np.where(overlapMask == 255)

        # 步骤2: 提取非重叠区域
        imA_diff = cv2.bitwise_and(imA, imA, mask=overlapMaskInv)
        imB_diff = cv2.bitwise_and(imB, imB, mask=overlapMaskInv)

        # 步骤3: 初始化权重矩阵
        G = self.get_mask(imA).astype(np.float32) / 255.0

        # 步骤4: 提取边界多边形
        polyA = self.get_outmost_polygon_boundary(imA_diff)
        polyB = self.get_outmost_polygon_boundary(imB_diff)

        # 步骤5: 计算每个重叠像素的权重
        for y, x in zip(*indices):
            xy_tuple = tuple([int(x), int(y)])
            distToB = cv2.pointPolygonTest(polyB, xy_tuple, True)  # 正数：内部   负数：轮廓外部

            if distToB < dist_threshold:
                distToA = cv2.pointPolygonTest(polyA, xy_tuple, True)
                distToB *= distToB  # 距离平方
                distToA *= distToA  # 距离平方
                G[y, x] = distToB / (distToA + distToB)  # 距离B轮廓越远权重越大

        return G, overlapMask

    def get_weights_and_masks(self):
        """
        计算四个重叠区域的融合权重和重叠区域掩膜
        :return:
        """
        front, back, left, right = self.images
        G0, M0 = self.get_weight_mask_matrix(FI(front, self.machine_range), LI(left, self.machine_range))
        G1, M1 = self.get_weight_mask_matrix(FII(front, self.machine_range), RII(right, self.machine_range))
        G2, M2 = self.get_weight_mask_matrix(BIII(back, self.machine_range), LIII(left, self.machine_range))
        G3, M3 = self.get_weight_mask_matrix(BIV(back, self.machine_range), RIV(right, self.machine_range))

        self.weights = [np.stack((G, G, G), axis=2) for G in (G0, G1, G2, G3)]
        self.masks = [(M / 255.0).astype(int) for M in (M0, M1, M2, M3)]

        return np.stack((G0, G1, G2, G3), axis=2), np.stack((M0, M1, M2, M3), axis=2)