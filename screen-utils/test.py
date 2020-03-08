from ssd1306desktop import framebuf
from ssd1306desktop import ssd1306img
from PIL import ImageTk

def callback(key,op):
    buf = memoryview(bytearray(128*64//8))
    print("key {:s}: {:s}".format(key,op))
    frame = framebuf.FrameBuffer(buf,128,64,framebuf.MONO_VLSB)
    frame.text("key {:s}: {:s}".format(key,op),0,0,1)
    from ssd1306desktop import screen_server
    screen_server.update_screen("main",buf)
    pass

def main():
    buf = memoryview(bytearray(128*64//8))
    frame = framebuf.FrameBuffer(buf,128,64,framebuf.MONO_VLSB)
    frame.text("Hello Dragon",0,0,1)
    frame.text("Hello World",0,8,1)
    frame.text("Hello Dragonssww",0,16,1)
    frame.text("Hello Dragon",0,24,1)
    frame.text("Hello Dragon",0,32,1)
    frame.text("Hello Dragon",0,40,1)
    frame.text("Hello Dragon",0,48,1)
    frame.text("Hello Dragon",0,56,1)
    img = ssd1306img.emu1306(buf,128,64,invert=True)
    # img.show()
    from ssd1306desktop import screen_server
    import time
    screen_server.setup_screen("main",128,64,buf,[
                "",      "up",        "",        "",       "A",
            "left",        "",   "right",        "",       "B",
                "",    "down",        "",        "",       "C",
    ],button_callback=callback)
    screen_server.start()
    try:
        while True:
            time.sleep(30)
            # print(screen_server.__get_image_data_url("main"))
    except:
        screen_server.stop()
        while screen_server.is_running():
            time.sleep(0.5)
    return True

if __name__ == "__main__":
    main()