import os
import os.path as osp

import yaml
import cv2
import numpy as np

from .utils import reshape_yaml_data, update_undistort_map


class fishEyeCamera:
    def __init__(self, cfg_path, camera_name):

        with open(cfg_path, 'r') as f:
            cfg = yaml.load(f, Loader=yaml.FullLoader)

        with open(osp.join(cfg["camera_yaml"], camera_name+".yaml"), 'r', encoding='utf-8') as cf:
            camera_cfg = yaml.load(cf, Loader=yaml.FullLoader)

        self.camera_matrix = reshape_yaml_data(camera_cfg, "camera_matrix")
        self.dist_coeffs = reshape_yaml_data(camera_cfg, "dist_coeffs")

        self.scale_xy = camera_cfg['scale_xy']['data']
        self.shift_xy = camera_cfg['shift_xy']['data']

        self.projection_matrix = reshape_yaml_data(camera_cfg, "projection_matrix")
        self.aerial_view_shape = camera_cfg['aerial_view_shape']


    def correct_distortion(self, img):
        h, w = img.shape[:2]
        new_matrix = update_undistort_map(self.camera_matrix, self.scale_xy, self.shift_xy)
        undistort_maps = cv2.fisheye.initUndistortRectifyMap(self.camera_matrix, self.dist_coeffs,
                                                             np.eye(3), new_matrix, (w, h), cv2.CV_16SC2)
        undistort_img = cv2.remap(img, *undistort_maps,
                           interpolation=cv2.INTER_LINEAR,  # 双线性插值
                           borderMode=cv2.BORDER_CONSTANT)  # 常数填充

        return undistort_img

    def perspective_projection(self,img):
        aerial_img = cv2.warpPerspective(img, self.projection_matrix, self.aerial_view_shape)

        return aerial_img