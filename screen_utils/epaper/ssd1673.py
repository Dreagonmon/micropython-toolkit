try:
    from utime import sleep_ms
except:
    from time import sleep_ms
try:
    import framebuf
    from micropython import const
except ImportError:
    from mgui.dev import framebuf
    def const(num):
        return num

# Rotaion
ROTATION_0 = const(0)
ROTATION_90 = const(1)
ROTATION_180 = const(2)
ROTATION_270 = const(3)
# Display resolution
EPD_WIDTH  = const(128)
EPD_HEIGHT = const(250)
EPD_OFFSET = const(6)
# datasheet says 122x250 (increased to 128 to be multiples of 8)

init_data = bytearray([
	0x50,0xAA,0x55,0xAA,0x55,0xAA,0x11,0x00,0x00,0x00,
	0x00,0x00,0x00,0x00,0x00,0x00,0x0F,0x0F,0x0F,0x0F,
	0x0F,0x0F,0x0F,0x01,0x00,0x00,0x00,0x00,0x00,
])

class EPD(framebuf.FrameBuffer):
    def __init__(self, spi, cs, dc, rst, busy, rotation=ROTATION_0, invert=True):
        #self.spi = espi = SPI(2, baudrate=20000000, sck=Pin(18), mosi=Pin(23), polarity=0, phase=0, firstbit=SPI.MSB)
        #self.spi = SPI(1, 8000000, sck=Pin(14), mosi=Pin(13), miso=Pin(12))
        self.spi = spi
        self.spi.init()
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.busy = busy
        self.cs.init(self.cs.OUT, value=1)
        self.dc.init(self.dc.OUT, value=0)
        self.rst.init(self.rst.OUT, value=0)
        self.busy.init(self.busy.IN, value=0)
        self.__rotation = rotation # can`t be changed later
        self.__invert = invert
        if self.__rotation == ROTATION_0 or self.__rotation == ROTATION_180:
            self.__width = EPD_WIDTH
            self.__height = EPD_HEIGHT
        else:
            self.__width = EPD_HEIGHT
            self.__height = EPD_WIDTH
        size = EPD_WIDTH * EPD_HEIGHT // 8
        self.buffer = memoryview(bytearray(size))
        super().__init__(self.buffer, self.__width, self.__height, framebuf.MONO_HLSB)
    @property
    def rotation(self):
        return self.__rotation
    @property
    def height(self):
        if self.__rotation == ROTATION_0 or self.__rotation == ROTATION_180:
            return EPD_HEIGHT
        else:
            return EPD_WIDTH - EPD_OFFSET
    @property
    def width(self):
        if self.__rotation == ROTATION_0 or self.__rotation == ROTATION_180:
            return EPD_WIDTH - EPD_OFFSET
        else:
            return EPD_HEIGHT
    
    def _wait_busy(self):
        while self.busy.value() == 1:
            sleep_ms(10)
    
    def _data(self, data):
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(data)
        self.cs(1)
    
    def _command(self, command, data=None):
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytes([command]))
        self.cs(1)
        if data is not None:
            self._data(data)
    
    def _write_lut(self):
        self._command(0x32, init_data[0:29])

    @micropython.native
    def _get_rotated_buffer(self):
        # no need to rotate
        if self.__rotation == ROTATION_0:
            return self.buffer
        # create buffer and rotate
        size = EPD_WIDTH * EPD_HEIGHT // 8
        fbuffer = memoryview(bytearray(size))
        frame = framebuf.FrameBuffer(fbuffer, EPD_WIDTH, EPD_HEIGHT, framebuf.MONO_HLSB)
        get_pixel = self.pixel
        set_pixel = frame.pixel
        # copy buffer
        if self.__rotation == ROTATION_270:
            for x in range(self.__width):
                for y in range(self.__height):
                    set_pixel(y, EPD_HEIGHT-x-1, get_pixel(x,y))
        if self.__rotation == ROTATION_90:
            for x in range(self.__width):
                for y in range(self.__height):
                    set_pixel(EPD_WIDTH-y-1-EPD_OFFSET, x, get_pixel(x,y))
        if self.__rotation == ROTATION_180:
            for x in range(self.__width):
                for y in range(self.__height):
                    set_pixel(EPD_WIDTH-x-1-EPD_OFFSET, EPD_HEIGHT-y-1, get_pixel(x,y))
        return fbuffer

    def _init(self):
        self.hard_reset()
        self._wait_busy()
        self._command(0x01, b'\xF9\x00');       # Gate Setting
        # self._data(0xF9);    # MUX Gate lines=250-1=249(F9H)
        # self._data(0x00);    # B[2]:GD=0[POR](G0 is the 1st gate output channel)  B[1]:SM=0[POR](left and right gate interlaced)  B[0]:TB=0[POR](scan from G0 to G319)
        self._command(0x3A, b'\x06');       # number of dummy line period   set dummy line for 50Hz frame freq
        # self._data(0x06);    # Set 50Hz   A[6:0]=06h[POR] Number of dummy line period in term of TGate
        self._command(0x3B, b'\x0B');       # Gate line width   set gate line for 50Hz frame freq
        # self._data(0x0B);    # A[3:0]=1011(78us)  Line width in us   78us*(250+6)=19968us=19.968ms
        self._command(0x3C, b'\x33');	      # Select border waveform for VBD
        #    self._data(0x30);    # GS0-->GS0
        #    self._data(0x31);    # GS0-->GS1
        #    self._data(0x32);    # GS1-->GS0
        # self._data(0x33);    # GS1-->GS1  开机第一次刷新Border从白到白
        #    self._data(0x43);    # VBD-->VSS
        #    self._data(0x53);    # VBD-->VSH
        #    self._data(0x63);    # VBD-->VSL
        #    self._data(0x73);    # VBD-->HiZ
        self._command(0x11, '\x03');	      # Data Entry mode
        # self._data(0x01);    # 01 –Y decrement, X increment
        self._command(0x44, b'\x00\x0F');       # set RAM x address start/end, in page 22
        # self._data(0x00);    # RAM x address start at 00h;
        # self._data(0x0f);    # RAM x address end at 0fh(15+1)*8->128    2D13
        self._command(0x45, b'\x00\xF9');	      # set RAM y address start/end, in page 22
        # self._data(0xF9);    # RAM y address start at FAh-1;		    2D13
        # self._data(0x00);    # RAM y address end at 00h;		    2D13
        self._command(0x2C, b'\x4B');       # Vcom= *(-0.02)+0.01???
        #    self._data(0x82);    #-2.5V
        #    self._data(0x69);    #-2V
        # self._data(0x4B);    #-1.4V
        #    self._data(0x50);    #-1.5V
        #    self._data(0x37);    #-1V
        #    self._data(0x1E);    #-0.5V
        self._write_lut()
        self.invert(self.__invert)
        self._wait_busy()

    def hard_reset(self):
        self.rst(0)
        sleep_ms(10)
        self.rst(1)
        sleep_ms(10)
    
    def deep_sleep(self):
        self._command(0x10, b'\x01')
    
    def update(self):
        self._init()
        self._command(0x4E, b'\x00')
        # self._data(0x00);  # set RAM x address count to 0;
        self._command(0x4F, b'\x00')
        # self._data(0xF9);  # set RAM y address count to 250-1;	2D13
        self._command(0x24, self._get_rotated_buffer())
        self._command(0x22, b'\xC7')
        # self._data(0xC7)    # (Enable Clock Signal, Enable CP) (Display update,Disable CP,Disable Clock Signal)
        #  SPI4W_WRITEDATA(0xF7)    # (Enable Clock Signal, Enable CP, Load Temperature value, Load LUT) (Display update,Disable CP,Disable Clock Signal)
        self._command(0x20)
        self._wait_busy()

    def invert(self, value=None):
        if value == None:
            return self.__invert
        if value:
            self._command(0x21, b'\x0C')
        else:
            self._command(0x21, b'\x00')
        self.__invert = value
