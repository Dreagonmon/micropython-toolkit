SET_COL_ADDR        = const(0x21)
SET_PAGE_ADDR       = const(0x22)
scr = None

def info(txt,line=0):
    #line 0 to 7
    scr.fill_rect(0, line*8, 128, 8, 0)
    scr.text(str(txt),0,line*8,1)
    refresh(0, line*8, 128, 8)
def text(x,y,text,clear=True):
    w = len(text)*8
    if clear:
        scr.fill_rect(x,y,w, 8, 0)
    scr.text(text,x,y,1)
    return w,8
def image(x,y,imgpath):
    with open(imgpath,'rb') as f:
        data = f.read()
    w = int(data[0])
    h = int(data[1])
    w,h = __sync(x,y,w,h,data[2:])
    return w,h
def show():
    scr.show()
def refresh(x=0,y=0,w=128,h=64):
    if y+h > scr.height:
        h = scr.height - y
    assert y % 8 == 0 and h % 8 == 0
    bp = y // 8 # base page
    pc = h // 8 # page count
    if x+w > scr.width:
        dw = scr.width - x
    else :
        dw = w # data width
    for p in range(pc):
        buf_start = (bp+p)*scr.width + x
        buf_end = buf_start+dw
        scr.write_cmd(SET_COL_ADDR)
        scr.write_cmd(buf_start)
        scr.write_cmd(buf_end-1)
        scr.write_cmd(SET_PAGE_ADDR)
        scr.write_cmd(bp+p)
        scr.write_cmd(bp+p-1)
        scr.write_data(scr.buffer[buf_start:buf_end])
    return dw,h
def __sync(x,y,w,h,data):
    if y+h > scr.height:
        h = scr.height - y
    assert y % 8 == 0 and h % 8 == 0
    bp = y // 8 # base page
    pc = h // 8 # page count
    if x+w > scr.width:
        dw = scr.width - x
    else :
        dw = w # data width
    for p in range(pc):
        buf_start = (bp+p)*scr.width + x
        data_start = p*w
        scr.buffer[buf_start:buf_start+dw] = data[data_start:data_start+dw]
    return dw,h
    
def init(scl=4,sda=5):
    global scr
    from machine import Pin,I2C
    from ssd1306 import SSD1306_I2C
    print("initing screen...")
    global i2c0,i2c1
    # i2c bus 0 screen
    scl0 = Pin(scl,Pin.IN,Pin.PULL_UP) #D2
    sda0 = Pin(sda,Pin.IN,Pin.PULL_UP) #D1
    i2c0 = I2C(-1,scl0,sda0)
    scr = SSD1306_I2C(128,64,i2c0)
    print("screen init done!")