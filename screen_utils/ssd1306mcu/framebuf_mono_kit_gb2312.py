'''
framebuf tool kit Module
'''
import framebuf
import coding, codecs_utf8_gb2312
from io import BytesIO
from math import ceil

TAB_SIZE = 4
ASCII_T = 9
ASCII_N = 10
ASCII_R = 13

FNT_16 = '/resource/HZK16S' # 16x16 32bytes
FNT_12 = '/resource/HZK12' # 12x12 24Byte
FNT_8 = '/resource/pix8x8.fnt' # 8x8 8Byte
CODEC_UTF8_GB2312 = '/resource/codecs_utf8_gb2312.bin'

# UNIVERSAL
def _draw_char_one_by_one(frame, x, y, width_limit, height_limit, font_size, chars_it, is_special_char, draw_char_on):
    moved_x = x
    moved_y = y
    for char in chars_it:
        if is_special_char(char, ASCII_T):
            char_count = (moved_x - x) // font_size
            lack_of_char = TAB_SIZE - char_count % TAB_SIZE
            lack_of_char = 0 if lack_of_char >= TAB_SIZE else lack_of_char
            moved_x += font_size * lack_of_char
        elif is_special_char(char, ASCII_R):
            moved_x = x
        elif is_special_char(char, ASCII_N) or (width_limit > 0 and moved_x + font_size - x > width_limit):
            moved_y += font_size
            moved_x = x
        if height_limit > 0 and (moved_y + font_size - y > height_limit):
            return
        if is_special_char(char, ASCII_T) or is_special_char(char, ASCII_N) or is_special_char(char, ASCII_R):
            continue
        draw_char_on(char, frame, moved_x, moved_y)
        moved_x += font_size

# GB2312
__fnt_16_fp = open(FNT_16, "rb")
__fnt_12_fp = open(FNT_12, "rb")
__fnt_8_fp = open(FNT_8, "rb")
__codec_u8_gb2312_fp = open(CODEC_UTF8_GB2312, "rb")
__codec_u8_gb2312 = codecs_utf8_gb2312.Codecs(__codec_u8_gb2312_fp)

def _gb2312_is_special_char(char, ascii):
    return char[0] == 0 and char[1] == ascii

def _draw_gb2312_text(text, frame, x, y, width_limit, height_limit, font_size, font_file_point):
    stream = BytesIO(__codec_u8_gb2312.from_string(text))
    reader = coding.GB2312Reader(stream)
    font_file_block_size = ceil(font_size / 8) * font_size
    def _gb2312_draw_char_on(char, frame, x, y):
        offset = coding.GB2312.to_dict_index(char) * font_file_block_size
        font_file_point.seek(offset)
        data_buf = bytearray(font_file_point.read(font_file_block_size))
        img = framebuf.FrameBuffer(data_buf, font_size, font_size, framebuf.MONO_HLSB)
        frame.blit(img, x, y, 0)
    _draw_char_one_by_one(frame, x, y, width_limit, height_limit, font_size, reader.chars(), _gb2312_is_special_char, _gb2312_draw_char_on)

def draw_gb2312_text_16(text, frame, x, y, width_limit=-1, height_limit=-1):
    return _draw_gb2312_text(text, frame, x, y, width_limit, height_limit, 16, __fnt_16_fp)

def draw_gb2312_text_12(text, frame, x, y, width_limit=-1, height_limit=-1):
    return _draw_gb2312_text(text, frame, x, y, width_limit, height_limit, 12, __fnt_12_fp)

def draw_gb2312_text_8(text, frame, x, y, width_limit=-1, height_limit=-1):
    return _draw_gb2312_text(text, frame, x, y, width_limit, height_limit, 8, __fnt_8_fp)
