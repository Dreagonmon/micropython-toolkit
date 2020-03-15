try:
    import utime
except:
    import time
    # timer 计算帧间隔用的工具类
    class Ticks(object):
        def __init__(self):
            self.last_time_ms = self.time_ms()
        def time_ms(self):
            return time.time_ns()//1000000
        def sleep_until_ms(self,ms):
            ct = self.time_ms()
            diff = ct - self.last_time_ms - ms
            while self.time_ms() - ct < diff:
                pass
            self.last_time_ms = self.last_time_ms + ms
        def is_passed_ms(self,ms):
            ct = self.time_ms()
            diff = ct - self.last_time_ms - ms
            if diff > 0:
                self.last_time_ms = self.last_time_ms + ms
                return True
            else:
                return False