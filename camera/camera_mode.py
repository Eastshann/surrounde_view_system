import cv2
import numpy as np
import yaml
from .utils import reshape_yaml_data, flip_camera

class FishEyeCamera:
    """
    鱼眼相机模型，通过配置文件和相机名，创建特定的相机模型
    功能：
    1. 鱼眼画面去畸变
    2. 去畸变后的画面，投影变换，生成鸟瞰视角
    """
    def __init__(self, cfg_path):

        #-----------------------------------------------------------------------------------
        # 相机参数配置

        with open(cfg_path, 'r') as f:
            cfg = yaml.load(f, Loader=yaml.FullLoader)

        # 内参矩阵
        self.camera_matrix = reshape_yaml_data(cfg, "camera_matrix")
        # 畸变系数
        self.dist_coeffs = reshape_yaml_data(cfg, "dist_coeffs")
        self.xi = np.array([[cfg['xi']]], dtype=np.float64)
        # 缩放和偏移
        self.scale_xy = cfg['scale_xy']['data']
        self.shift_xy = cfg['shift_xy']['data']
        # 投影矩阵
        self.projection_matrix = reshape_yaml_data(cfg, "project_matrix")
        # 矫正图尺寸
        self.shape = cfg['resolution']['data']
        # 鸟瞰图尺寸
        self.aerial_view_shape = cfg['project_resolution']['data']
        # -----------------------------------------------------------------------------------

    def update_undistort_map(self, camera_matrix, scale, shift):
        """
        根据缩放系数，生成校正映射表
        :param camera_matrix: 元素内参矩阵
        :param scale: 缩放系数
        :param shift: 平移系数
        :return: 校正映射表
        """
        new_matrix = camera_matrix.copy()

        # 应用缩放参数
        new_matrix[0, 0] *= scale[0]
        new_matrix[1, 1] *= scale[1]

        # 应用平移参数
        new_matrix[0, 2] += shift[0]
        new_matrix[1, 2] += shift[1]

        return new_matrix

    def undistort_display(self, img):
        """
        矫正图像
        :param img: 待矫正图片
        :return:
        """
        # 调整映射表
        new_matrix = self.update_undistort_map(self.camera_matrix, self.scale_xy, self.shift_xy)

        # 调整校正后的视角
        undistort_maps = cv2.omnidir.initUndistortRectifyMap(self.camera_matrix, self.dist_coeffs,
                                                             self.xi,
                                                             np.eye(3),
                                                             new_matrix,
                                                             self.shape,
                                                             cv2.CV_16SC2,
                                                             cv2.omnidir.RECTIFY_PERSPECTIVE)
        # 校正画面
        result = cv2.remap(img, *undistort_maps,
                           interpolation=cv2.INTER_LINEAR,  # 双线性插值
                           borderMode=cv2.BORDER_CONSTANT)  # 常数填充

        return result

    def perspective_projection(self,img):
        """
        投影变换，生成鸟瞰图
        :param img:
        :return:
        """
        aerial_img = cv2.warpPerspective(img, self.projection_matrix, self.aerial_view_shape)

        return aerial_img

    def flip_cam(self, img, camera_name):
        flipped_img = flip_camera(img, camera_name)
        return flipped_img