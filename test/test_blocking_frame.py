"""
测试阻塞式 get_frame() 功能
直接测试 DahuaStream 的 get_frame(wait_for_new=True) 方法
"""
from camera import DahuaStream
import time
import threading

def test_blocking_get_frame():
    """测试阻塞式获取帧"""
    print("="*60)
    print("测试阻塞式 get_frame() 功能")
    print("="*60)
    
    # 创建相机实例
    dahua = DahuaStream(
        camera_name="back",
        ip="192.168.110.12",
        port=37777,
        username="admin",
        password="xy123456",
        channel=0,
        stream_type="sub"
    )
    
    # 启动相机流
    try:
        dahua.print_stream_info()
        dahua.init_sdk()
        dahua.login()
        dahua.start_stream()
        
        print("相机流启动成功，开始测试阻塞式获取帧...")
        print("预期：每次 get_frame() 调用应该等待新帧到达")
        print("="*50)
        
        frame_count = 0
        start_time = time.time()
        
        for i in range(100):  # 测试获取100帧
            # 使用阻塞式获取帧
            frame = dahua.get_frame(wait_for_new=True, timeout=2.0)
            frame_count += 1
            
            current_time = time.time()
            elapsed = current_time - start_time
            
            if frame_count % 10 == 0:  # 每10帧打印一次
                fps = frame_count / elapsed
                print(f"已获取 {frame_count} 帧，平均FPS: {fps:.2f}")
            
            # 如果超过5秒，停止测试
            if elapsed > 5.0:
                break
        
        final_time = time.time()
        total_elapsed = final_time - start_time
        final_fps = frame_count / total_elapsed
        
        print("="*50)
        print(f"测试完成:")
        print(f"总帧数: {frame_count}")
        print(f"总时间: {total_elapsed:.2f} 秒")
        print(f"平均FPS: {final_fps:.2f}")
        print(f"预期FPS应该接近相机实际帧率（约25帧）")
        print("="*50)
        
    except KeyboardInterrupt:
        print("\n用户中断测试")
    except Exception as e:
        print(f"测试出错: {e}")
    finally:
        dahua.stop()
        print("相机资源已清理")

if __name__ == "__main__":
    test_blocking_get_frame()
