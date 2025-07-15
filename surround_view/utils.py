import numpy as np


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

def update_undistort_map(camera_matrix, scale, shift):
    """
    生成校正映射表
    :param camera_matrix: 元素内参矩阵
    :param scale: 缩放系数
    :param shift: 平移系数
    :return: 校正映射表
    """
    new_matrix = camera_matrix.copy()

    # 应用缩放参数
    new_matrix[0,0] *= scale[0]
    new_matrix[1,1] *= scale[1]

    # 应用平移参数
    new_matrix[0,2] += shift[0]
    new_matrix[1,2] += shift[1]

    return new_matrix