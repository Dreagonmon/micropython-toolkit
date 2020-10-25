from ssd1306desktop.screen_server import MonoScreenEmu
from ssd1306desktop.framebuf import FrameBuffer, MONO_VLSB
from ticks import Ticks
try:
    from ubinascii import a2b_base64
except:
    from binascii import a2b_base64

DATA_24_24_VEEMON1 = "HBwkxMTYHBwbGxsExMTEBATEBATY4OAAAACAgIAIt7fBQEDHT09JQEBAwcHIR0c+Dg4dERHyn5+dkJCR8vJ+8PCek5OR/v4A"
DATA_24_24_VEEMON2 = "ODjYGBggODgkJCQYGBgYGBgYGBggwMAAAAAAAQExTk6GgICOv7+3gICBhoaxj494HBxyYmLs/v7z4eHj7e194eH97+/j/f0A"

screen:MonoScreenEmu = None
def is_key_down(key):
    if screen==None:
        return False
    return screen.is_key_down(key)

class Drawable(object):
    level = 0
    x = y = width = height = 0
    def draw(self,fbuf):
        raise NotImplementedError()
    def box_hit_with(self,drawable):
        if (self.x >= drawable.x+drawable.width
            or self.x+self.width <= drawable.x
            or self.y >= drawable.y+drawable.height
            or self.y+self.height <= drawable.y):
            return False
        return True

class Veemon(Drawable):
    def __init__(self,x,y,storage):
        self.x = x
        self.y = y
        self.width = 24
        self.height = 24
        self.__storage = storage
        self.frame1 = FrameBuffer(bytearray(a2b_base64(DATA_24_24_VEEMON1)),24,24,MONO_VLSB)
        self.frame2 = FrameBuffer(bytearray(a2b_base64(DATA_24_24_VEEMON2)),24,24,MONO_VLSB)
        self.current = self.frame1
        self.__tick = Ticks()
        self.__last_move = self.__tick.time_ms()
    def draw(self,fbuf):
        fbuf.blit(self.current,self.x,self.y)
        # animation
        if self.__tick.is_passed_ms(500):
            if self.current == self.frame1:
                self.current = self.frame2
            else:
                self.current = self.frame1
        # move 100pix / s
        ct = self.__tick.time_ms()
        duration = ct - self.__last_move
        self.__last_move = ct
        dist = duration // 10
        if is_key_down("up") or is_key_down("down") or is_key_down("left") or is_key_down("right"):
            if dist > 0:
                if is_key_down("up"):
                    self.y = self.y - dist
                if is_key_down("down"):
                    self.y = self.y + dist
                if is_key_down("left"):
                    self.x = self.x - dist
                if is_key_down("right"):
                    self.x = self.x + dist
                if self.x < 0: 
                    self.x = 0
                if self.x > 104: 
                    self.x = 104
                if self.y < 8: 
                    self.y = 8
                if self.y > 40: 
                    self.y = 40
                
class Road(Drawable):
    def __init__(self,storage):
        self.x = 0
        self.y = 8
        self.width = 128
        self.height = 56
        self.__storage = storage
        self.frame = FrameBuffer(bytearray(128*56//8),128,56,MONO_VLSB)
        self.offset = 64
        self.__tick = Ticks()
    def update(self):
        self.frame.fill(0)
        self.frame.fill_rect(-32+self.offset,24,32,8,1)
        self.frame.fill_rect(32+self.offset,24,32,8,1)
        self.frame.fill_rect(96+self.offset,24,32,8,1)
    def draw(self,fbuf):
        self.update()
        fbuf.blit(self.frame,self.x,self.y)
        if self.__tick.is_passed_ms(50):
            # road moving speed 20pix/s
            self.offset = self.offset - 1
            if self.offset < 0:
                self.offset = 64

def main():
    global screen
    screen = MonoScreenEmu(128,64,name="main")
    # buttons=[
    #             "",      "up",        "",        "",       "A",
    #         "left",    "down",   "right",       "B",        "",
    #             "",        "",        "",        "",       "C",
    # ]
    screen.register_key(1,"up")
    screen.register_key(4,"A")
    screen.register_key(5,"left")
    screen.register_key(6,"down")
    screen.register_key(7,"right")
    screen.register_key(8,"B")
    screen.register_key(14,"C")
    # main loop
    storage = {}
    storage["objs"] = []
    road = Road(storage)
    storage["objs"].append(road)
    veemon = Veemon(0,40,storage)
    storage["objs"].append(veemon)
    tick = Ticks()
    storage["last_frame_time"] = tick.time_ms()
    try:
        while True:
            ct = tick.time_ms()
            storage["duration"] = ct - storage["last_frame_time"]
            storage["last_frame_time"] = ct
            screen.fill(0)
            screen.text("Hello Dragon",0,0,1)
            for drawable in storage["objs"]:
                drawable.draw(screen)
            screen.show()
            tick.sleep_until_ms(50)
    except:
        # import traceback
        # traceback.print_exc()
        pass
    return True

if __name__ == "__main__":
    main()