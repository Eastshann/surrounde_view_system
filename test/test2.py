from camera import FishEyeCamera
import cv2

def get_aerial(bgr_frame, mode, camera_name):

    undistort_frame = mode.undistort_display(bgr_frame)
    aerial_frame = mode.perspective_projection(undistort_frame)
    flip_frame = mode.flip_cam(aerial_frame, camera_name)

    return flip_frame

camera_list = ["front", "back", "left", "right"]
# 捕获线程
mode_list = [FishEyeCamera(f"../cfgs/{camera_name}.yaml") for camera_name in camera_list]

front_img = cv2.imread(r"D:\Projects\Work\06_dahua_surround\test\imgs\front.png")
back_img = cv2.imread(r"D:\Projects\Work\06_dahua_surround\test\imgs\back.png")
left_img = cv2.imread(r"D:\Projects\Work\06_dahua_surround\test\imgs\left.png")
right_img = cv2.imread(r"D:\Projects\Work\06_dahua_surround\test\imgs\right.png")

new_front = get_aerial(front_img, mode_list[0], "front")
new_back = get_aerial(back_img, mode_list[1], "back")
new_left = get_aerial(left_img, mode_list[2], "left")
new_right = get_aerial(right_img, mode_list[3], "right")

cv2.imwrite("./imgs/aerial_view/new_front.jpg", new_front)
cv2.imwrite("./imgs/aerial_view/new_back.jpg", new_back)
cv2.imwrite("./imgs/aerial_view/new_left.jpg", new_left)
cv2.imwrite("./imgs/aerial_view/new_right.jpg", new_right)

