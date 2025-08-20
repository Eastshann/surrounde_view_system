import cv2
import numpy as np

import time
import threading

# 导入大华SDK
from NetSDK.NetSDK import NetClient
from NetSDK.SDK_Callback import fDisConnect, fHaveReConnect, fDecCBFun, fRealDataCallBackEx2
from NetSDK.SDK_Enum import SDK_RealPlayType, EM_LOGIN_SPAC_CAP_TYPE, EM_REALDATA_FLAG
from NetSDK.SDK_Struct import *

class DahuaStream:
    def __init__(self, ip="192.168.110.11", port=37777, username="admin", password="xy123456",
                 channel=0, stream_type="main"):
        # 相机名
        # self.camera_mode = FishEyeCamera(r"/cfgs/surrount.yaml", camera_name)
        # 相机参数
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.channel = channel

        # 码流配置
        self.stream_type = stream_type.lower()
        self.stream_config = self._get_stream_config()

        # SDK变量
        self.sdk = NetClient()
        self.loginID = 0
        self.playID = 0
        self.freePort = c_int()

        # 视频帧
        self.current_frame = None
        self.undistort_frame = None
        self.aerial_view_frame = None
        self.frame_lock = threading.Lock()
        self.running = False
        self.use_playsdk = False  # 标记是否使用PlaySDK

        self.update_time = time.time()

        # 统计信息
        self.frame_count = 0
        self.last_time = time.time()

        # 设置回调
        self.setup_callbacks()

    def _get_stream_config(self):
        """获取码流配置"""
        stream_configs = {
            "main": {
                "type": SDK_RealPlayType.Realplay,
                "name": "主码流",
                "description": "高清晰度主码流，适用于录像和高质量预览"
            },
            "sub": {
                "type": SDK_RealPlayType.Realplay_1,
                "name": "辅码流",
                "description": "低码率辅码流，适用于网络传输和移动设备预览"
            }
        }

        if self.stream_type not in stream_configs:
            print(f"⚠ 不支持的码流类型: {self.stream_type}，使用默认主码流")
            self.stream_type = "main"

        config = stream_configs[self.stream_type]
        print(f"✓ 码流配置: {config['name']} - {config['description']}")
        return config

    def get_stream_info(self):
        """
        获取当前码流信息
        """
        return {
            "type": self.stream_type,
            "name": self.stream_config["name"],
            "description": self.stream_config["description"],
            "channel": self.channel,
            "running": self.running
        }

    def print_stream_info(self):
        """打印码流信息"""
        info = self.get_stream_info()
        print("\n=== 当前码流信息 ===")
        print(f"码流类型: {info['name']}")
        print(f"描述: {info['description']}")
        print(f"通道: {info['channel']}")
        print(f"运行状态: {'运行中' if info['running'] else '已停止'}")
        print(f"相机地址: {self.ip}:{self.port}")
        print("=" * 30)

    def setup_callbacks(self):
        """
        设置回调函数
        """
        self.disconnect_cb = fDisConnect(self.on_disconnect)
        self.reconnect_cb = fHaveReConnect(self.on_reconnect)
        self.decode_cb = fDecCBFun(self.on_decode)
        self.data_cb = fRealDataCallBackEx2(self.on_data)

    def on_disconnect(self, loginID, ip, port, user):
        """
        断线回调
        """
        print("⚠ 设备断线")

    def on_reconnect(self, loginID, ip, port, user):
        """
        重连回调
        """
        print("✓ 设备重连")
        
    def init_h264_decoder(self):
        """初始化H.264解码器"""
        try:
            # 创建H.264解码器
            fourcc = cv2.VideoWriter_fourcc(*'H264')
            self.decoder = cv2.VideoCapture()
            
            # 设置解码器参数
            self.decoder.set(cv2.CAP_PROP_FOURCC, fourcc)
            self.decoder.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            print("✓ H.264解码器初始化成功")
            return True
        except Exception as e:
            print(f"✗ H.264解码器初始化失败: {e}")
            return False


    def on_data(self, handle, dataType, buffer, bufSize, param, user):
        """
        数据回调，接收来自相机的原始视频数据流（通常是H.264编码的数据）
        在混合模式下，将原始数据传递给PlaySDK进行解码
        在纯回调模式下，可以自定义处理这些原始数据
        """
        if handle == self.playID:
            if self.use_playsdk and hasattr(self, 'freePort'):
                # 混合模式：将数据送入PlaySDK解码
                try:
                    self.sdk.InputData(self.freePort, buffer, bufSize)
                except:
                    # 忽略InputData错误
                    pass
            else:
                # 纯回调模式：直接处理原始数据
                # 这里可以添加自定义的H.264解码逻辑
                pass

    def on_decode(self, port, buf, size, frameInfo, userData, reserved):
        """
        解码回调 - 只在混合模式下被调用
        接收PlaySDK解码后的视频帧数据（YUV格式）
        只在混合模式下工作，因为需要PlaySDK先解码原始数据
        将YUV数据转换为OpenCV可用的BGR格式
        更新当前帧供显示使用
        """
        try:
            info = frameInfo.contents
            # print(info.nWidth, info.nHeight)
            if info.nType == 3:  # YUV数据
                # 获取帧数据
                yuv_data = cast(buf, POINTER(c_ubyte * size)).contents
                yuv_array = np.frombuffer(yuv_data, dtype=np.uint8)

                # 转换为BGR
                bgr_frame = self.yuv420_to_bgr(yuv_array, info.nWidth, info.nHeight)

                if bgr_frame is not None:
                    with self.frame_lock:
                        # 原始画面
                        self.current_frame = bgr_frame
                        # # 矫正画面
                        # self.undistort_frame = self.camera_mode.undistort_display(bgr_frame)
                        # # 鸟瞰画面
                        # self.aerial_view_frame = self.camera_mode.perspective_projection(self.undistort_frame)

                        self.frame_count += 1
                        self.update_time = time.time()

                        # 显示帧率
                        current_time = time.time()
                        if current_time - self.last_time >= 1.0:
                            fps = self.frame_count / (current_time - self.last_time)
                            # print(f"FPS: {fps:.1f}")
                            self.frame_count = 0
                            self.last_time = current_time
        except:
            pass

    def yuv420_to_bgr(self, yuv_data, width, height):
        """YUV420转BGR"""
        try:
            y_size = width * height
            uv_size = y_size // 4

            if len(yuv_data) < y_size + 2 * uv_size:
                return None

            # 提取YUV分量
            y = yuv_data[:y_size].reshape((height, width))
            u = yuv_data[y_size:y_size + uv_size].reshape((height // 2, width // 2))
            v = yuv_data[y_size + uv_size:y_size + 2 * uv_size].reshape((height // 2, width // 2))

            # 上采样UV
            u = cv2.resize(u, (width, height))
            v = cv2.resize(v, (width, height))

            # 合并YUV
            yuv = np.stack([y, u, v], axis=2)

            # 转换为BGR
            rgb = cv2.cvtColor(yuv, cv2.COLOR_YUV2RGB)
            bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

            return bgr
        except:
            return None

    def init_sdk(self):
        """
        初始化SDK
        """
        result = self.sdk.InitEx(self.disconnect_cb)
        if result:
            self.sdk.SetAutoReconnect(self.reconnect_cb)
            print("✓ SDK初始化成功")
            return True
        else:
            print("✗ SDK初始化失败")
            return False

    def login(self):
        """登录相机"""
        login_in = NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY()
        login_in.dwSize = sizeof(NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY)
        login_in.szIP = self.ip.encode()
        login_in.nPort = self.port
        login_in.szUserName = self.username.encode()
        login_in.szPassword = self.password.encode()
        login_in.emSpecCap = EM_LOGIN_SPAC_CAP_TYPE.TCP

        login_out = NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY()
        login_out.dwSize = sizeof(NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY)

        print(f"正在连接相机 {self.ip}:{self.port}...")
        self.loginID, device_info, error = self.sdk.LoginWithHighLevelSecurity(login_in, login_out)

        if self.loginID != 0:
            print(f"✓ 登录成功! 通道数: {device_info.nChanNum}")
            return True
        else:
            print(f"✗ 登录失败: {error}")
            return False

    def start_stream(self):
        """启动视频流 - 智能模式选择"""
        print("正在启动视频流...")
        print(f"通道: {self.channel}, 码流: {self.stream_config['name']}")

        # 方案1：尝试混合模式（推荐）
        if self.start_hybrid_mode():
            return True

        # 方案2：如果混合模式失败，尝试纯回调模式
        print("混合模式失败，尝试纯回调模式...")
        return self.start_callback_only_mode()

    def start_hybrid_mode(self):
        """
        混合模式：PlaySDK + CallBack
        """
        try:
            # 获取播放端口
            result, self.freePort = self.sdk.GetFreePort()
            if not result:
                print("✗ 获取播放端口失败")
                return False

            print(f"获取播放端口: {self.freePort.value}")

            # 初始化PlaySDK
            self.sdk.OpenStream(self.freePort)
            self.sdk.Play(self.freePort, 0)  # 不显示到窗口

            # 启动实时预览 - 使用配置的通道和码流类型
            stream_type = self.stream_config["type"]
            self.playID = self.sdk.RealPlayEx(self.loginID, self.channel, 0, stream_type)

            if self.playID != 0:
                # 设置回调
                self.sdk.SetRealDataCallBackEx2(self.playID, self.data_cb, None, EM_REALDATA_FLAG.RAW_DATA)
                self.sdk.SetDecCallBack(self.freePort, self.decode_cb)

                self.use_playsdk = True
                self.running = True
                print(f"✓ 混合模式启动成功 - {self.stream_config['name']}")
                return True
            else:
                print(f"✗ RealPlayEx失败: {self.sdk.GetLastErrorMessage()}")
                return False

        except Exception as e:
            print(f"✗ 混合模式异常: {e}")
            return False

    def start_callback_only_mode(self):
        """纯回调模式：只使用数据回调"""
        try:
            # 初始化H.264解码器
            self.init_h264_decoder()
            
            # 直接启动实时预览，不使用PlaySDK - 使用配置的通道和码流类型
            stream_type = self.stream_config["type"]
            self.playID = self.sdk.RealPlayEx(self.loginID, self.channel, 0, stream_type)

            if self.playID != 0:
                # 只设置数据回调
                self.sdk.SetRealDataCallBackEx2(self.playID, self.data_cb, None, EM_REALDATA_FLAG.RAW_DATA)

                self.use_playsdk = False
                self.running = True
                print(f"✓ 纯回调模式启动成功 - {self.stream_config['name']}")
                return True
            else:
                print(f"✗ 纯回调模式失败: {self.sdk.GetLastErrorMessage()}")
                return False
        except Exception as e:
            print(f"✗ 纯回调模式失败: {self.sdk.GetLastErrorMessage()}")
            return False

    def show_video(self):
        """显示视频"""
        window_title = f'origin'
        undistort_window_title = f'undistort'
        aerial_window_title = f'aerial'
        print(f"视频显示中... 按 'q' 退出, 按 's' 截图, 按 'i' 显示码流信息")

        no_frame_count = 0
        while self.running:
            with self.frame_lock:
                if self.current_frame is not None:
                    cv2.imshow(window_title, self.current_frame)
                    cv2.imshow(undistort_window_title, self.undistort_frame)
                    cv2.imshow(aerial_window_title,self.aerial_view_frame)
                    no_frame_count = 0
                else:
                    no_frame_count += 1
                    if no_frame_count > 100:  # 约3秒无帧
                        print("⚠ 长时间无视频帧，请检查网络连接")
                        no_frame_count = 0

            key = cv2.waitKey(30) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                if self.current_frame is not None:
                    timestamp = int(time.time())
                    filename = f"capture_{self.stream_type}_ch{self.channel}_{timestamp}.jpg"
                    cv2.imwrite(filename, self.current_frame)
                    print(f"截图保存: {filename}")
            elif key == ord('i'):
                self.print_stream_info()

        cv2.destroyAllWindows()

    def stop(self):
        """停止并清理"""
        self.running = False

        if self.playID:
            self.sdk.StopRealPlayEx(self.playID)

            if self.use_playsdk and hasattr(self, 'freePort'):
                self.sdk.SetDecCallBack(self.freePort, None)
                self.sdk.Stop(self.freePort)
                self.sdk.CloseStream(self.freePort)
                self.sdk.ReleasePort(self.freePort)

        if self.loginID:
            self.sdk.Logout(self.loginID)

        self.sdk.Cleanup()
        print("✓ 资源清理完成")

    def get_frame(self):
        """
        获取当前帧

        """
        # 非阻塞模式，直接返回当前帧
        with self.frame_lock:
            if self.current_frame is not None:
                return self.update_time, self.current_frame.copy()  # 返回副本避免并发修改
            else:
                # 返回一个黑色占位图像，避免cv2.imshow错误
                return self.update_time, np.zeros((480, 640, 3), dtype=np.uint8)

    def run(self):
        try:
            self.print_stream_info()
            self.init_sdk()
            self.login()
            self.start_stream()
            self.show_video()

        except KeyboardInterrupt:
            print("\n用户中断")
        except Exception as e:
            print(f"错误: {e}")
        finally:
            self.stop()

    def run2(self):
        try:
            self.print_stream_info()
            self.init_sdk()
            self.login()
            self.start_stream()
            while self.running:
                with self.frame_lock:
                    if self.current_frame is not None:
                        # print(self.current_frame.shape)
                        cv2.imshow("sss", self.undistort_frame)

                # 添加 waitKey 以更新窗口显示
                key = cv2.waitKey(30) & 0xFF
                if key == ord('q'):
                    break

        except KeyboardInterrupt:
            print("\n用户中断")
        except Exception as e:
            print(f"错误: {e}")
        finally:
            self.stop()
            cv2.destroyAllWindows()  # 清理窗口
