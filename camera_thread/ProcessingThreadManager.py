import threading
import numpy as np
from .Buffer import Buffer

class ProcessingThreadManager(object):
    def __init__(self, num_cams, drop_if_full=True, buffer_size=8):
        self.drop_if_full = drop_if_full    # 是否非阻塞

        self.sync_devices = set()
        self.mutex = threading.Lock()
        # 线程屏障，供所有摄像头线程同步使用
        self.num_cams = num_cams
        self.barrier = threading.Barrier(num_cams)
        self.current_frames = dict()  # 当前帧缓存
        self.buffer = Buffer(buffer_size)
        self.count = 0


    def bind_thread(self, thread):
        with self.mutex:
            self.sync_devices.add(thread.device_id)
        # 初始化帧缓存
        shape = thread.camera_mode.aerial_view_shape
        self.current_frames[thread.device_id] = np.zeros(tuple(shape[::-1]) + (3,), np.uint8)
        # 绑定
        thread.proc_buffer_manager = self
        print(f"已绑定{thread.camera_name}处理线程")

    def get(self):
        return self.buffer.get()

    def set_frame_for_device(self, device_id, frame):
        """
        存储图片到current_frames
        :param device_id:
        :param frame:
        :return:
        """
        if device_id not in self.sync_devices:
            raise ValueError("Device not held by the buffer: {}".format(device_id))

        self.current_frames[device_id] = frame

    def sync(self):
        try:
            # 等待所有线程到达屏障
            self.count += 1
            if self.count == self.num_cams:
                # 将current_frames存入缓冲
                self.buffer.add(self.current_frames, self.drop_if_full)
                self.count = 0
            # 唤醒所有线程
            self.barrier.wait()



        except threading.BrokenBarrierError:
            # 如果屏障被破坏（线程异常退出），这里防止程序崩溃
            pass
