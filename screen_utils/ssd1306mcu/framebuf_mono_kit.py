'''
framebuf tool kit Module
'''
import framebuf
import coding, ubmfont
from io import BytesIO
from math import ceil

TAB_SIZE = 4
ASCII_T = 9
ASCII_N = 10
ASCII_R = 13

UNICODE_FNT_16 = '/resource/pix16x16.ufnt'
UNICODE_FNT_8 = '/resource/pix8x8.ufnt'

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

def get_text_line(text, width_limit, size=8):
    # unicode also ok!
    moved_x = 0
    lines = 1
    for char in text:
        if char == '\n' or (width_limit > 0 and moved_x + size > width_limit):
            lines += 1
            moved_x = 0
        if char == '\n' or char == '\r':
            moved_x = 0
            continue
        moved_x += size
    return lines

# UNICODE
__unicode_font_query_16 = ubmfont.FontQuery(open(UNICODE_FNT_16, 'rb'))
__unicode_font_query_8 = ubmfont.FontQuery(open(UNICODE_FNT_8, 'rb'))

def _unicode_is_special_char(char, ascii):
    return char == ascii

def _draw_unicode_text(text, frame, x, y, width_limit, height_limit, font_size, font_query):
    stream = BytesIO(text.encode("utf8"))
    reader = coding.UTF8Reader(stream)
    def _unicode_draw_char_on(char, frame, x, y):
        data_buf = font_query.query(char)
        if data_buf == None:
            return
        img = framebuf.FrameBuffer(data_buf, font_size, font_size, framebuf.MONO_HLSB)
        frame.blit(img, x, y, 0)
    _draw_char_one_by_one(frame, x, y, width_limit, height_limit, font_size, reader.chars(), _unicode_is_special_char, _unicode_draw_char_on)

def draw_unicode_text_16(text, frame, x, y, width_limit=-1, height_limit=-1):
    return _draw_unicode_text(text, frame, x, y, width_limit, height_limit, 16, __unicode_font_query_16)

def draw_unicode_text_8(text, frame, x, y, width_limit=-1, height_limit=-1):
    return _draw_unicode_text(text, frame, x, y, width_limit, height_limit, 8, __unicode_font_query_8)

# ASCII
def _ascii_is_special_char(char, ascii):
    return char.encode("utf8")[0] == ascii

def draw_ascii_text_8(text, frame, x, y, width_limit=-1, height_limit=-1):
    def _ascii_draw_char_on(char, frame, x, y):
        frame.text(char, x, y, 1)
    _draw_char_one_by_one(frame, x, y, width_limit, height_limit, 8, text, _ascii_is_special_char, _ascii_draw_char_on)

# Console
class Console():
    def __init__(self, frame, width, height, show_function=None):
        self.__print_y = 0
        self.__print_frame = frame
        self.__print_frame_width = width
        self.__print_frame_height = height
        self.__show_f = show_function
    def log(self, *args, show=True):
        txts = []
        for t in args:
            txts.append(str(t))
        text = ' '.join(txts)
        lines = get_text_line(text, self.__print_frame_width, 8)
        new_y = self.__print_y + lines * 8
        if new_y > self.__print_frame_height:
            offset = new_y - self.__print_frame_height
            self.__print_y -= offset
            self.__print_frame.scroll(0, 0-offset)
            new_y = self.__print_frame_height
        self.__print_frame.fill_rect(0, self.__print_y, self.__print_frame_width, lines * 8, 0)
        draw_ascii_text_8(text, self.__print_frame, 0, self.__print_y, self.__print_frame_width, self.__print_frame_height)
        self.__print_y = new_y
        if self.__show_f != None and show:
            self.__show_f()
    def clear(self, *_, show=True):
        self.__print_frame.fill_rect(0, 0, self.__print_frame_width, self.__print_frame_height, 0)
        self.__print_y = 0
        if self.__show_f != None and show:
            self.__show_f()
