import cv2

from surround_view import fishEyeCamera

cfg_path = "yamls/cfg.yaml"
font = fishEyeCamera(cfg_path, "front")

img = cv2.imread("images/front.png")
undistort_img = font.correct_distortion(img)

aerial_img = font.perspective_projection(undistort_img)

cv2.imshow("aerial_img", aerial_img)
cv2.waitKey(0)
cv2.destroyAllWindows()
