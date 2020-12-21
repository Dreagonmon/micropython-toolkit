''' use unicode bitmap font (custom defined format) '''

''' // c int to bytes
#define FAST_ABS(x) ((x ^ (x>>31)) - (x>>31))

int is_big_endian(void)
{
    union {
        uint32_t i;
        char c[4];
    } bint = {0x01020304};

    return bint.c[0] == 1; 
}    

uint32_t num = 0xAABBCCDD;
uint32_t N = is_big_endian() * 3;

printf("first byte 0x%02X\n"
       "second byte 0x%02X\n"
       "third byte 0x%02X\n"
       "fourth byte 0x%02X\n",
       ((unsigned char *) &num)[FAST_ABS(3 - N)],
      ((unsigned char *) &num)[FAST_ABS(2 - N)],
      ((unsigned char *) &num)[FAST_ABS(1 - N)],
      ((unsigned char *) &num)[FAST_ABS(0 - N)]
       );
'''

import sys, os

current_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(current_path)
sys.path.append(os.path.join(current_path, "..", "..", "text_utils", "coding"))
sys.path.append(os.path.join(current_path, "..", "ssd1306desktop"))

import ubmfont, coding, framebuf

if __name__ == "__main__":
    testf = open(os.path.join(current_path, ".." , "out", "pix10x10.ufnt"), 'rb')
    fq = ubmfont.FontQuery(testf)
    w, h = fq.get_font_size()
    for ch in "龙龍你好风神翼龙":
        char_unicode = coding.UTF8.from_bytes(ch.encode("utf8"))
        font_data = fq.query(char_unicode)
        if font_data != None:
            frame = framebuf.FrameBuffer(font_data, w, h, framebuf.MONO_HLSB)
            print(frame)
    pass
