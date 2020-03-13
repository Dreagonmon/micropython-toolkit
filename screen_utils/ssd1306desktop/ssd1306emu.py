from . import framebuf, screen_server

class SSD1306_EMU(framebuf.FrameBuffer):
    def __init__(self,width,height,name="main",buttons=[],button_callback=None):
        assert width <= 128 and width >= 2
        assert height <= 64 and height >= 2
        self.width = width
        self.height = height
        self.pages = self.height // 8
        self.buffer = memoryview(bytearray(self.pages * self.width))
        self.screen = memoryview(bytearray(self.pages * self.width))
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.name = name
        self.is_invert = True
        self.buttons = buttons
        self.button_callback = button_callback
        self.init_display()

    def init_display(self):
        screen_server.start()
        screen_server.setup_screen(self.name,self.width,self.height,self.screen,invert=self.is_invert,buttons=self.buttons,button_callback=self.button_callback)
        pass

    def poweroff(self):
        for x in range(self.width):
            for p in range(self.pages):
                self.screen[p*self.width + x] = 0
        screen_server.update_screen(self.name,self.screen)

    def poweron(self):
        for x in range(self.width):
            for p in range(self.pages):
                self.screen[p*self.width + x] = self.buffer[p*self.width + x]
        screen_server.update_screen(self.name,self.screen)

    def contrast(self, contrast):
        pass

    def invert(self, invert):
        self.is_invert = not self.is_invert
        self.init_display()
        screen_server.update_screen(self.name,self.screen)
    
    def show(self):
        for x in range(self.width):
            for p in range(self.pages):
                self.screen[p*self.width + x] = self.buffer[p*self.width + x]
        screen_server.update_screen(self.name,self.screen)
    
    def refresh(self,x,y,w,h):
        p0 = y // 8
        p1 = (y+h) // 8
        if (y+h) % 8 != 0:
            p1 = p1 + 1
        for x in range(x,x+w):
            for p in range(p0,p1):
                self.screen[p*self.width + x] = self.buffer[p*self.width + x]
        screen_server.update_screen(self.name,self.screen)