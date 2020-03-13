from ssd1306desktop import framebuf
from ssd1306desktop.ssd1306emu import SSD1306_EMU
from PIL import ImageTk
frame:SSD1306_EMU = None
def callback(key,op):
    print("key {:s}: {:s}".format(key,op))
    frame.fill_rect(0,0,128,8,0)
    frame.text("key {:s}: {:s}".format(key,op),0,0,1)
    frame.refresh(0,0,128,8)
    pass

def main():
    global frame
    frame = SSD1306_EMU(128,64,name="main",buttons=[
                "",      "up",        "",        "",       "A",
            "left",    "down",   "right",       "B",        "",
                "",        "",        "",        "",       "C",
    ],button_callback=callback)
    frame.text("Hello Dragon",0,0,1)
    frame.text("Hello World",0,8,1)
    frame.text("Hello Dragonssww",0,16,1)
    frame.text("Hello Dragon",0,24,1)
    frame.text("Hello Dragon",0,32,1)
    frame.text("Hello Dragon",0,40,1)
    frame.text("Hello Dragon",0,48,1)
    frame.text("Hello Dragon",0,56,1)
    frame.show()
    import time
    try:
        while True:
            time.sleep(30)
            # print(screen_server.__get_image_data_url("main"))
    except:
        pass
    return True

if __name__ == "__main__":
    main()