from . import framebuf

class SSD1306_EMU(framebuf.FrameBuffer):
    def __init__(self,width,height,asyncLoop):
        assert width <= 128 and width >= 2
        assert height <= 64 and height >= 2
        self.width = width
        self.height = height
        self.pages = self.height // 8
        self.buffer = memoryview(bytearray(self.pages * self.width))
        self.screen = memoryview(bytearray(self.pages * self.width))
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

    def init_display(self):
        # 
        pass
