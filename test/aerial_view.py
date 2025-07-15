import numpy as np
import cv2

undistort_img = cv2.imread("undistort.jpg")
undistort_img2 = undistort_img.copy()

aerial_view_shape = (1200,550)

#--------------------------------------------------------------
# 目标点
# 顺时针方向
p_a = [420,300]
p_b = [780.,300]
p_c = [780.,460.]
p_d = [420.,460.]
dst = [p_a, p_b, p_c, p_d]
src = []

#--------------------------------------------------------------
# 鼠标回调函数
def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        src.append([x, y])
        cv2.circle(undistort_img, (x, y), 3, (0, 0, 255), -1)

#--------------------------------------------------------------
# 创建窗口并绑定鼠标事件
cv2.namedWindow("Image")
cv2.namedWindow("aerail_Image")
cv2.setMouseCallback("Image", mouse_callback)

while True:
    cv2.imshow("Image", undistort_img)
    key = cv2.waitKey(1)
    if key == 27:  # 按 ESC 键退出
        break

    if key == ord('s'):
        cv2.imwrite("aerial_img.jpg", aerial_img)

    if key == ord('c'):
        if len(src) == 4:
            matrix = cv2.getPerspectiveTransform(np.array(src, dtype=np.float32),
                                                 np.array(dst, dtype=np.float32))
            print(matrix)
            aerial_img = cv2.warpPerspective(undistort_img2, matrix, aerial_view_shape)
            cv2.imshow("aerail_Image", aerial_img)
        else:
            print("请先点击图像选择 4 个点")