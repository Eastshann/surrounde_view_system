import cv2
import numpy as np
from surround_view import update_undistort_map

# 相机内参
camera_matrix = np.array([[3.0245305983229298e+02, 0.0,                    4.9664001463163459e+02],
                          [0.0,                    3.2074618594392325e+02, 3.3119980984361649e+02],
                          [0.0,                    0.0,                    1.0]])
# 畸变系数
dist_coeffs = np.array([-4.3735601598704078e-02, 2.1692522970939803e-02, -2.6388839028513571e-02, 8.4123126605702321e-03])

img = cv2.imread("../images/front.png")
if img is None:
    raise FileNotFoundError("找不到图片 images/front.png")

h, w = img.shape[:2]

# 初始参数
scale = [0.7, 0.8]
shift = [-150, -100]

def undistort_display(scale, shift):
    new_matrix = update_undistort_map(camera_matrix, scale, shift)
    # 调整校正后的视角
    undistort_maps = cv2.fisheye.initUndistortRectifyMap(camera_matrix, dist_coeffs, np.eye(3), new_matrix, (w, h), cv2.CV_16SC2)
    # 校正画面
    result = cv2.remap(img, *undistort_maps,
                       interpolation=cv2.INTER_LINEAR, # 双线性插值
                       borderMode=cv2.BORDER_CONSTANT) # 常数填充
    return result

while True:
    result = undistort_display(scale, shift)
    save_img = result.copy()
    display_text = f"scale: {scale}, shift: {shift}"
    cv2.putText(result, display_text, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.imshow("result", result)

    key = cv2.waitKey(0) & 0xFF

    if key == 27:  # ESC 退出
        break
    elif key == ord('9'):
        scale[0] -= 0.01
    elif key == ord('0'):
        scale[0] += 0.01
    elif key == ord('-'):
        scale[1] -= 0.01
    elif key == ord('='):  # 注意 = 和 + 在同一键上
        scale[1] += 0.01
    elif key == ord('['):
        shift[0] -= 5
    elif key == ord(']'):
        shift[0] += 5
    elif key == ord(';'):
        shift[1] -= 5
    elif key == ord('\''):
        shift[1] += 5

    elif key == ord('s'):
        cv2.imwrite("undistort.jpg", save_img)
        print(img)
        print("save")

cv2.destroyAllWindows()
