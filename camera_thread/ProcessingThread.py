import threading
import time

class ProcessingThread(threading.Thread):
    def __init__(self,
                 capture_thread_manager,    # 捕获缓冲管理器
                 device_id,                 # 设备id
                 camera_name,               # 相机名称
                 camera_mode,               # 相机模型
                 drop_if_full,              # 是否非阻塞
                 parent = None):
        super(ProcessingThread, self).__init__(parent)
        self.capture_thread_manager = capture_thread_manager
        self.device_id = device_id
        self.camera_name = camera_name
        self.camera_mode = camera_mode
        self.drop_if_full = drop_if_full

        self.proc_buffer_manager = None     # 处理缓冲管理器
        self.running = False

        # FPS统计用变量
        self.fps_counter = {
            "frames": 0,
            "start_time": time.time()
        }

    def run(self):
        # 未绑定报警
        if self.proc_buffer_manager is None:
            raise ValueError("This thread has not been binded to any processing thread yet")

        if not self.running:
            self.running = True
            print(f"{self.camera_name}处理线程启动")

        while True:
            bgr_frame = self.capture_thread_manager.get_device_buffer(self.device_id).get()
            # cv2.imwrite(f"{self.camera_name}.jpg", bgr_frame)
            # print(bgr_frame.shape)

            # 去畸变
            undistort_frame = self.camera_mode.undistort_display(bgr_frame)
            # 鸟瞰图
            aerial_frame = self.camera_mode.perspective_projection(undistort_frame)
            # 翻转
            flip_frame = self.camera_mode.flip_cam(aerial_frame,self.camera_name)

            # 存入图片
            self.proc_buffer_manager.set_frame_for_device(self.device_id, flip_frame)

            # 统计fps
            # self.count_fps()

            # 同步
            self.proc_buffer_manager.sync()



    def count_fps(self):
        """
        统计fps，每秒统计一次
        :param start_time:
        :param frame_count:
        :return:
        """
        # 统计帧量
        self.fps_counter["frames"] += 1
        elapsed_time = time.time() - self.fps_counter["start_time"]

        if elapsed_time >= 1.0:
            fps = self.fps_counter["frames"] / elapsed_time
            print(f"当前FPS: {fps:.2f}")
            self.fps_counter["frames"] = 0
            self.fps_counter["start_time"] = time.time()

