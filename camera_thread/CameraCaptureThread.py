import threading
import time
import yaml
from camera import DahuaStream

class CameraCaptureThread(threading.Thread):
    def __init__(self, camera_name):
        super().__init__()

        with open(f'../cfgs/{camera_name}.yaml', 'r') as f:
            config = yaml.safe_load(f)

        # 相机编号
        self.camera_name = camera_name
        self.device_id = config['device_id']

        # 登录配置
        self.ip = config['ip']
        self.port = config['port']
        self.username = config['username']
        self.password = config['password']
        self.channel = config['channel']
        self.stream_type = config['stream_type']

        # 捕获线程管理器
        self.buffer_manager = None
        self.drop_if_full = True

        self.running = False

        # FPS统计用变量
        self.fps_counter = {
            "frames": 0,
            "start_time": time.time()
        }

        self.update_time = None

        self.dahua = DahuaStream(
            ip=self.ip,
            port=self.port,
            username=self.username,
            password=self.password,
            channel=self.channel,
            stream_type=self.stream_type)

        # 启动视频流
        self.dahua.print_stream_info()
        self.dahua.init_sdk()
        self.dahua.login()
        self.dahua.start_stream()




    def run(self):
        if not self.running:
            self.running = True
            print(f"{self.camera_name}捕获线程启动")

        while self.running:
            # Step 1: 等待所有线程到达
            self.buffer_manager.sync()

            # Step 2: 同步采集图像 - 等待新帧
            update_time, frame = self.dahua.get_frame()

            if self.update_time == update_time:
                continue
            self.update_time = update_time

            # 统计fps
            # self.count_fps()

            # Step 3: 载入缓冲
            self.buffer_manager.get_device_buffer(self.device_id).add(frame, self.drop_if_full)

    def stop(self):
        self.dahua.stop()
        self.running = False

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