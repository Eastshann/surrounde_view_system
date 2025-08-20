from camera import DahuaStream

dahua = DahuaStream(
            camera_name = "back",
            ip="192.168.110.12",
            port=37777,
            username="admin",
            password="xy123456",
            channel=0,
            stream_type="sub")

dahua.run2()