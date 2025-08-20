import cv2
import numpy as np
import os
import os.path as osp

def flip_camera(img, camera_name):
    """
    旋转不同视角的画面
    :param img:
    :param camera_name:
    :return:
    """
    if camera_name == 'back':
        img = cv2.rotate(img, cv2.ROTATE_180)
    elif camera_name == 'left':
        img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif camera_name == 'right':
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)

    return img

def reshape_yaml_data(data, key_name):
    """将yaml数据还原"""
    if data[key_name]["rows"] > 1:
        reshaped_data = np.array(data[key_name]["data"]).reshape(
            data[key_name]["rows"],
            data[key_name]["cols"]
        )
    else:
        reshaped_data = np.array(data[key_name]["data"])

    return reshaped_data

def tune(x):
    if x >= 1:
        return x * np.exp((1 - x) * 0.5)
    else:
        return x * np.exp((1 - x) * 0.8)


def mean_luminance_ratio(grayA, grayB, mask):
    """
    计算两个灰度图像在指定区域内的平均亮度比值
    :param grayA: 第一个灰度图像（单通道）
    :param grayB: 第二个灰度图像（单通道）
    :param mask: 掩码矩阵，值为0或1，定义计算区域
    :return:
    """
    return get_mean_statistisc(grayA, mask) / get_mean_statistisc(grayB, mask)

def get_mean_statistisc(gray, mask):
    """
    只保留掩码区域内的像素值（掩码为1的区域）
    """
    return np.sum(gray * mask)

def adjust_luminance(gray, factor):
    """
    按指定系数调整灰度图像的亮度
    """
    return np.minimum((gray * factor), 255).astype(np.uint8)

def make_white_balance(image):
    """
    根据图像各通道的平均值调整其白平衡。
    """
    B, G, R = cv2.split(image)
    # 每个通道的平均亮度
    m1 = np.mean(B)
    m2 = np.mean(G)
    m3 = np.mean(R)
    # 全局平均亮度
    K = (m1 + m2 + m3) / 3
    # 调整值
    c1 = K / m1
    c2 = K / m2
    c3 = K / m3
    # 应用调整
    B = adjust_luminance(B, c1)
    G = adjust_luminance(G, c2)
    R = adjust_luminance(R, c3)

    return cv2.merge((B, G, R))

#------------------------------------------------------------
# 前
def FI(img, machine_range):
    x_left, x_right, y_top, y_bottom = machine_range
    return img[:, :x_left]

def FM(img, machine_range):
    x_left, x_right, y_top, y_bottom = machine_range
    return img[:, x_left:x_right]

def FII(img, machine_range):
    x_left, x_right, y_top, y_bottom = machine_range
    return img[:, x_right:]

# ------------------------------------------------------------
# 后
def BIII(img, machine_range):
    x_left, x_right, y_top, y_bottom = machine_range
    # img = cv2.rotate(img, cv2.ROTATE_180)
    img = img[: , :x_left]

    return img

def BM(img, machine_range):
    x_left, x_right, y_top, y_bottom = machine_range
    # img = cv2.rotate(img, cv2.ROTATE_180)
    img = img[:, x_left:x_right]

    return img

def BIV(img, machine_range):
    x_left, x_right, y_top, y_bottom = machine_range
    # img = cv2.rotate(img, cv2.ROTATE_180)
    img = img[:, x_right:]

    return img

# ------------------------------------------------------------
# 左
def LI(img, machine_range):
    x_left, x_right, y_top, y_bottom = machine_range
    # img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    img = img[:y_top, :]

    return img

def LM(img, machine_range):
    x_left, x_right, y_top, y_bottom = machine_range
    # img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    img = img[y_top:y_bottom, :]

    return img

def LIII(img, machine_range):
    x_left, x_right, y_top, y_bottom = machine_range
    # img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    img = img[y_bottom:, :]

    return img



# ------------------------------------------------------------
# 右
def RII(img, machine_range):
    # print(f"裁剪前：{img.shape}")
    x_left, x_right, y_top, y_bottom = machine_range
    # img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    img = img[:y_top, :]
    # print(f"裁剪后：{img.shape}")

    return img

def RM(img, machine_range):
    x_left, x_right, y_top, y_bottom = machine_range
    # img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    img = img[y_top:y_bottom, :]

    return img

def RIV(img, machine_range):
    x_left, x_right, y_top, y_bottom = machine_range
    # img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    img = img[y_bottom:, :]

    return img

