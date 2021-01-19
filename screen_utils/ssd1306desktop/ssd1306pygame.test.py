try:
    import framebuf
    from ssd1306pygame import SSD1306_Emu
except ImportError:
    from . import framebuf
    from .ssd1306pygame import SSD1306_Emu
from binascii import a2b_base64
from time import sleep

DATA_24_24_VEEMON1 = "HBwkxMTYHBwbGxsExMTEBATEBATY4OAAAACAgIAIt7fBQEDHT09JQEBAwcHIR0c+Dg4dERHyn5+dkJCR8vJ+8PCek5OR/v4A"
DATA_24_24_VEEMON2 = "ODjYGBggODgkJCQYGBgYGBgYGBggwMAAAAAAAQExTk6GgICOv7+3gICBhoaxj494HBxyYmLs/v7z4eHj7e194eH97+/j/f0A"
VEEMON1 = framebuf.FrameBuffer(bytearray(a2b_base64(DATA_24_24_VEEMON1)),24,24,framebuf.MONO_VLSB)
VEEMON2 = framebuf.FrameBuffer(bytearray(a2b_base64(DATA_24_24_VEEMON2)),24,24,framebuf.MONO_VLSB)

if __name__ == "__main__":
    print("==== run test ====")
    screen = SSD1306_Emu(128, 64)
    try:
        count = 0
        while True:
            screen.fill(0)
            screen.text("{}".format(count), 0, 0, 1)
            count += 1
            screen.text("  Hello Dragon  ", 0, 8, 1)
            screen.blit(VEEMON1, 52, 24, 0)
            screen.show()
            # print("show1")
            screen.pygame_loop(True)
            screen.fill(0)
            screen.text("{}".format(count), 0, 0, 1)
            count += 1
            screen.text("  Hello Veemon  ", 0, 8, 1)
            screen.blit(VEEMON2, 52, 24, 0)
            screen.show()
            # print("show2")
            # screen.pygame_loop(False)
    except KeyboardInterrupt:
        print("Stoped.")
