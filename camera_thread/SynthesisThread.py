import threading
import yaml

import cv2
import numpy as np
from PIL import Image
from camera import SurroundView
from .Buffer import Buffer
import time

class SynthesisThread(threading.Thread):
    """
    合成线程
    功能：
    1. 处理线程管理器中获取处理好的画面
    2. 合成画面
    """
    def __init__(self,
                 processing_thread_manager,
                 cfg_path,
                 drop_if_full=True,
                 buffer_size=8,
                 parent = None):
        super(SynthesisThread, self).__init__(parent)
        # 处理线程管理器
        self.processing_thread_manager = processing_thread_manager
        self.drop_if_full = drop_if_full    # 是否非阻塞
        self.buffer = Buffer(buffer_size)   # 缓冲队列
        self.mutex = threading.Lock()       # 线程锁

        self.image = None   # 环视图
        self.frames = None  # 帧

        # FPS统计用变量
        self.fps_counter = {
            "frames": 0,
            "start_time": time.time()
        }
        self.cfg_path = cfg_path    # 配置文件路径
        with open(self.cfg_path, 'r') as f:
            cfg = yaml.safe_load(f)

        self.masks_path = cfg['masks_path']
        self.weights_path = cfg['weights_path']
        self.masks = None
        self.weights = None
        self.load_weights_and_masks(self.weights_path, self.masks_path)


    def load_weights_and_masks(self, weights_image, masks_image):
        GMat = np.asarray(Image.open(weights_image).convert("RGBA"), dtype=np.float64) / 255.0
        self.weights = [np.stack((GMat[:, :, k],
                                  GMat[:, :, k],
                                  GMat[:, :, k]), axis=2)
                        for k in range(4)]

        Mmat = np.asarray(Image.open(masks_image).convert("RGBA"), dtype=np.float64)
        Mmat = (Mmat.astype(np.float64) / 255.0).astype(int)
        self.masks = [Mmat[:, :, k] for k in range(4)]

    def run(self):
        while True:
            self.frames = self.processing_thread_manager.get()

            front = self.frames[0]
            back  = self.frames[1]
            left  = self.frames[2]
            right = self.frames[3]

            surround_view = SurroundView(self.masks, self.weights, self.cfg_path)
            surround_view.make_luminance_balance([front, back, left, right])
            surround_view.stitch_all_parts()
            self.image = surround_view.image

            self.image = cv2.resize(self.image, (900, 900))




            # result = np.vstack((front, back))

            # 统计时间
            self.count_fps()

            # print(result.shape)
            cv2.imshow("result",self.image)
            cv2.waitKey(1)

    def count_fps(self):
        """
        统计fps，每秒统计一次
        :param start_time:
        :param frame_count:
        :return:
        """
        # 统计帧量
        self.fps_counter["frames"] += 1
        elapsed_time =  time.time() - self.fps_counter["start_time"]

        if elapsed_time >= 1.0:
            fps = self.fps_counter["frames"] / elapsed_time
            print(f"当前FPS: {fps:.2f}")
            self.fps_counter["frames"] = 0
            self.fps_counter["start_time"] = time.time()