import threading
import time

from .Buffer import Buffer

class CaptureThreadManager:
    def __init__(self, num_cams, do_sync=True):
        # 同步设备列表
        self.sync_devices = set()
        self.mutex = threading.Lock()
        # 线程屏障，供所有摄像头线程同步使用
        self.barrier = threading.Barrier(num_cams)
        self.buffer_maps = dict()
    #----------------------------------------------------------------------
    # 绑定线程，并创建缓冲
    def create_buffer_for_device(self, device_id, buffer_size, sync=True):
        """
        为设备创建图片缓冲区
        :param device_id: 设备编号
        :param buffer_size: 缓冲区大小
        :param sync: 是否是同步设备
        :return:
        """
        if sync:
            with self.mutex:
                self.sync_devices.add(device_id)

        self.buffer_maps[device_id] = Buffer(buffer_size)

    def bind_thread(self, thread, buffer_size, sync=True):
        """
        绑定捕获线程到捕获管理器
        :param thread: 捕获线程
        :param buffer_size: 缓冲区大小
        :param sync: 是否是同步设备
        :return:
        """
        # 给设备创建缓冲队列
        self.create_buffer_for_device(thread.device_id, buffer_size, sync)
        # 绑定线程到管理器
        thread.buffer_manager = self
        print(f"已绑定{thread.camera_name}捕获线程")

    # ----------------------------------------------------------------------
    def get_device_buffer(self, device_id):
        """
        获取设备对应的图片缓冲区
        :param device_id:
        :return:
        """
        return self.buffer_maps[device_id]

    def remove_device(self, device_id):
        """
        删除设备对应的图片缓冲区
        :param device_id: 设备编号
        :return:
        """
        self.buffer_maps.pop(device_id, None)

        with self.mutex:
            if device_id in self.sync_devices:
                self.sync_devices.remove(device_id)

    def sync(self):
        """
        屏障机制同步
        :return:
        """
        try:
            # 等待所有线程到达屏障
            self.barrier.wait()
        except threading.BrokenBarrierError:
            # 如果屏障被破坏（线程异常退出），这里防止程序崩溃
            pass


