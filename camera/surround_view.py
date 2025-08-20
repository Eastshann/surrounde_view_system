import cv2
import numpy as np
import yaml

from .utils import *

class SurroundView:
    def __init__(self, masks, weights, cfg_path):
        # 四个重叠区域的掩膜
        self.masks = masks
        # 四个重叠区域的融合权重
        self.weights = weights
        self.frames = []

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
        # 全景图尺寸
        # self.total_w = machine_w + 2*inner_w + 2*board_w + 2*shift_w
        # self.total_h = machine_h + 2*inner_h + 2*board_h + 2*shift_h
        self.total_w = 1200
        self.total_h = 1200
        # 全景图
        self.image = np.zeros((self.total_h, self.total_w, 3), np.uint8)
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



    # ------------------------------------------------------------
    def make_luminance_balance(self, frames):
        """
        亮度平衡
        :param frames: 同一时刻的四个视角画面
        :return:
        """
        front, back, left, right = frames
        m1, m2, m3, m4 = self.masks
        # 色彩通道分离
        Fb, Fg, Fr = cv2.split(front)
        Bb, Bg, Br = cv2.split(back)
        Lb, Lg, Lr = cv2.split(left)
        Rb, Rg, Rr = cv2.split(right)
        # 计算重叠区域平均亮度比
        b1 = mean_luminance_ratio(FI(Fb, self.machine_range), LI(Lb, self.machine_range), m1)
        g1 = mean_luminance_ratio(FI(Fg, self.machine_range), LI(Lg, self.machine_range), m1)
        r1 = mean_luminance_ratio(FI(Fr, self.machine_range), LI(Lr, self.machine_range), m1)

        b2 = mean_luminance_ratio(RII(Rb, self.machine_range), FII(Fb, self.machine_range), m2)
        g2 = mean_luminance_ratio(RII(Rg, self.machine_range), FII(Fg, self.machine_range), m3)
        r2 = mean_luminance_ratio(RII(Rr, self.machine_range), FII(Fr, self.machine_range), m3)

        b3 = mean_luminance_ratio(LIII(Lb, self.machine_range), BIII(Bb, self.machine_range), m3)
        g3 = mean_luminance_ratio(LIII(Lg, self.machine_range), BIII(Bg, self.machine_range), m3)
        r3 = mean_luminance_ratio(LIII(Lr, self.machine_range), BIII(Br, self.machine_range), m3)

        b4 = mean_luminance_ratio(BIV(Bb, self.machine_range), RIV(Rb, self.machine_range), m4)
        g4 = mean_luminance_ratio(BIV(Bg, self.machine_range), RIV(Rg, self.machine_range), m4)
        r4 = mean_luminance_ratio(BIV(Br, self.machine_range), RIV(Rr, self.machine_range), m4)
        # 计算亮度调整系数
        b = (b1 * b2 * b3 * b4) ** 0.25
        g = (g1 * g2 * g3 * g4) ** 0.25
        r = (r1 * r2 * r3 * r4) ** 0.25
        # ------------------------------------------------------------
        # 调整front
        Fbx = b / (b1 / b2) ** 0.5
        Fgx = g / (g1 / g2) ** 0.5
        Frx = r / (r1 / r2) ** 0.5

        Fbx = tune(Fbx)
        Fgx = tune(Fgx)
        Frx = tune(Frx)

        Fb = adjust_luminance(Fb, Fbx)
        Fg = adjust_luminance(Fg, Fgx)
        Fr = adjust_luminance(Fr, Frx)
        # ------------------------------------------------------------
        # 调整back
        Bbx = b / (b4 / b3) ** 0.5
        Bgx = g / (g4 / g3) ** 0.5
        Brx = r / (r4 / r3) ** 0.5

        Bbx = tune(Bbx)
        Bgx = tune(Bgx)
        Brx = tune(Brx)

        Bb = adjust_luminance(Bb, Bbx)
        Bg = adjust_luminance(Bg, Bgx)
        Br = adjust_luminance(Br, Brx)
        # ------------------------------------------------------------
        # 调整left
        Lbx = b / (b3 / b1) ** 0.5
        Lgx = g / (g3 / g1) ** 0.5
        Lrx = r / (r3 / r1) ** 0.5

        Lbx = tune(Lbx)
        Lgx = tune(Lgx)
        Lrx = tune(Lrx)

        Lb = adjust_luminance(Lb, Lbx)
        Lg = adjust_luminance(Lg, Lgx)
        Lr = adjust_luminance(Lr, Lrx)
        # ------------------------------------------------------------
        # 调整right
        Rbx = b / (b2 / b4) ** 0.5
        Rgx = g / (g2 / g4) ** 0.5
        Rrx = r / (r2 / r4) ** 0.5

        Rbx = tune(Rbx)
        Rgx = tune(Rgx)
        Rrx = tune(Rrx)

        Rb = adjust_luminance(Rb, Rbx)
        Rg = adjust_luminance(Rg, Rgx)
        Rr = adjust_luminance(Rr, Rrx)

        # 合并色彩通道
        self.frames = [cv2.merge((Fb, Fg, Fr)),
                       cv2.merge((Bb, Bg, Br)),
                       cv2.merge((Lb, Lg, Lr)),
                       cv2.merge((Rb, Rg, Rr))]

    def merge(self, imA, imB, k):
        """
        根据权重合并重叠区域
        :param imA:
        :param imB:
        :param k: 重叠区域编号
        :return:
        """
        G = self.weights[k]
        return (imA * G + imB * (1 - G)).astype(np.uint8)

    @property
    def FL(self):
        return self.image[:self.y_top, :self.x_left]

    @property
    def F(self):
        return self.image[:self.y_top, self.x_left:self.x_right]

    @property
    def FR(self):
        return self.image[:self.y_top, self.x_right:]

    @property
    def BL(self):
        return self.image[self.y_bottom:, :self.x_left]

    @property
    def B(self):
        return self.image[self.y_bottom:, self.x_left:self.x_right]

    @property
    def BR(self):
        return self.image[self.y_bottom:, self.x_right:]

    @property
    def L(self):
        return self.image[self.y_top:self.y_bottom, :self.x_left]

    @property
    def R(self):
        return self.image[self.y_top:self.y_bottom, self.x_right:]

    @property
    def C(self):
        return self.image[self.y_top:self.y_bottom, self.x_left:self.x_right]

    def stitch_all_parts(self):
        """
        将处理的好的画面，覆盖到全景图上
        :return:
        """
        front, back, left, right = self.frames
        np.copyto(self.F, FM(front, self.machine_range))
        np.copyto(self.B, BM(back, self.machine_range))
        np.copyto(self.L, LM(left, self.machine_range))
        np.copyto(self.R, RM(right, self.machine_range))
        np.copyto(self.FL, self.merge(FI(front, self.machine_range), LI(left, self.machine_range), 0))
        np.copyto(self.FR, self.merge(FII(front, self.machine_range), RII(right, self.machine_range), 1))
        np.copyto(self.BL, self.merge(BIII(back, self.machine_range), LIII(left, self.machine_range), 2))
        np.copyto(self.BR, self.merge(BIV(back, self.machine_range), RIV(right, self.machine_range), 3))


    def make_white_balance(self):
        """
        白平衡
        :return:
        """
        self.image = make_white_balance(self.image)
