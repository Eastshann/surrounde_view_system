from camera_thread import *
from camera import FishEyeCamera

camera_list = ["front", "back", "left", "right"]
mode_list = [FishEyeCamera(f"../cfgs/{camera_name}.yaml") for camera_name in camera_list]

# 捕获线程
cc_td_list = [CameraCaptureThread(camera_name) for camera_name in camera_list]

capture_thread_manager = CaptureThreadManager(4)

for td in cc_td_list:
    capture_thread_manager.bind_thread(td, 8)
    td.start()

# 处理线程
p_td_list = [ProcessingThread(capture_thread_manager,
                              td.device_id,
                              td.camera_name,
                              mode,
                    True)
             for td, mode in zip(cc_td_list, mode_list)]

processing_thread_manager = ProcessingThreadManager(4)

for td in p_td_list:
    processing_thread_manager.bind_thread(td)
    td.start()

# 合成线程
synthesis_td = SynthesisThread(processing_thread_manager,r"D:\Projects\Work\06_dahua_surround\cfgs\surround.yaml")
synthesis_td.start()






