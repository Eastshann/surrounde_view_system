import threading
from queue import Queue

class Buffer(object):
    """
    数据缓冲队列
    功能：
    1. 数据入队，队列满时可选是否丢弃数据，有锁防止clear时add
    2. 数据出队
    3. 清空队列，有锁防止循环出队中间被add
    """
    def __init__(self, buffer_size=5):

        self.lock = threading.Lock()
        self.queue = Queue(buffer_size)

    def add(self, data, drop_if_full=False):
        with self.lock:
            # 当缓冲区满时是否丢弃新数据而不阻塞
            if drop_if_full and self.queue.full():
                return
            self.queue.put(data)

    def get(self):
        return self.queue.get()


    def clear(self):
        with self.lock:
            while not self.queue.empty():
                self.queue.get()

    def size(self):
        return self.queue.qsize()
