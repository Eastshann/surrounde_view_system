"""
测试帧同步功能
验证 get_frame(wait_for_new=True) 是否能正确阻塞等待新帧
"""
from camera_thread import *
from camera import FishEyeCamera
import time

print("="*60)
print("测试帧同步功能")
print("="*60)

#-------------------------------------------------------------------------------
# 相机模型
front = FishEyeCamera("../cfgs/surround.yaml", "front")
back = FishEyeCamera("../cfgs/surround.yaml", "back")

#-------------------------------------------------------------------------------
# 捕获线程
front_capture_td = CameraCaptureThread("front")
back_capture_td = CameraCaptureThread("back")

print("="*50)

capture_thread_manager = CaptureThreadManager(2)

capture_thread_manager.bind_thread(front_capture_td,8)
capture_thread_manager.bind_thread(back_capture_td,8)

print("="*50)

front_capture_td.start()
back_capture_td.start()

#-------------------------------------------------------------------------------
# 处理线程
front_processing_td = ProcessingThread(capture_thread_manager,
                                       front_capture_td.device_id,
                                       front_capture_td.camera_name,
                                       front,
                                       True)

back_processing_td = ProcessingThread(capture_thread_manager,
                                       back_capture_td.device_id,
                                        back_capture_td.camera_name,
                                       back,
                                       True)

processing_thread_manager = ProcessingThreadManager(2)

print("="*50)

processing_thread_manager.bind_thread(front_processing_td)
processing_thread_manager.bind_thread(back_processing_td)

print("="*50)

front_processing_td.start()
back_processing_td.start()

synthesis_td = SynthesisThread(processing_thread_manager)
synthesis_td.start()

print("="*60)
print("帧同步测试启动完成")
print("预期结果：synthesis_td 的帧数应该接近相机的实际帧率（约25帧）")
print("按 Ctrl+C 停止测试")
print("="*60)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n测试结束")
