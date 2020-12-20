''' 生成自定义格式的unicode点阵字体
FILE:
[magic_word_u:1B] [max_unicode_size:1B]
[font_width:1B] [font_height:1B]
[INDEX_AREA...]

INDEX_AREA:
[this_area_count:2B] [this_area_type:1B] [index_match_size:1B]
[INDEX_MATCH...]
[INDEX_DATA...]
- index match are in order, from small to large. index_match -> index_data, using same index
- this_area_type:
    0x00 font_data_index_area, index data is font data, size depends on font width and height
    0x01 4_bytes_offset_index_area, index data is 4bytes offset, next_area_address = offset + base

INDEX_MATCH:
[match_byte:1B]

INDEX_DATA:
[offset_or_font_data:?B]
'''
import sys, os

current_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(current_path, "..", "..", "text_utils", "coding"))
sys.path.append(os.path.join(current_path, "..", "ssd1306desktop"))
# sys.path.append(os.path.join(current_path, "..", "utils"))

from PIL import Image, ImageFont, ImageDraw
import math
import coding, framebuf

def _get_char_data(char_str, block_w, block_h, fnt, position_offset=(0, 0), invert=False):
    block_size = math.ceil(block_w / 8) * block_h
    char_left, char_top, char_right, char_bottom = fnt.getbbox(char_str)
    char_width = char_right - char_left
    char_height = char_bottom - char_top
    char_x_offset = (block_w - char_width) // 2
    # char align to center bottom
    if char_bottom <= block_h - 1:
        char_y_offset = char_top
    elif char_height >= block_h * 0.95:
        # simplely remove top margin
        char_y_offset = 0
    else:
        char_y_offset = block_h - 1 - char_height
    char_offset = (position_offset[0] + char_x_offset, position_offset[1] + char_y_offset)
    # draw char
    fnt_img = Image.new("1", (block_w, block_h), color=255)
    fnt_draw = ImageDraw.Draw(fnt_img)
    try:
        fnt_draw.text(char_offset, char_str, fill=0, font=fnt, anchor="lt", spacing=0)
    except: pass
    # draw framebuffer
    buffer = bytearray(block_size)
    frame = framebuf.FrameBuffer(buffer, block_w, block_h, framebuf.MONO_HLSB)
    for y in range(block_h):
        for x in range(block_w):
            pixel = fnt_img.getpixel((x, y))
            pixel = 1 if ((pixel == 0) ^ invert) else 0
            frame.pixel(x, y, pixel)
    # print(frame)
    # fnt_img.save('l.png')
    return buffer, fnt_img

class IndexArea():
    def __init__(self, area_type, index_match_size=1, index_data_size=0):
        assert area_type in [0x00, 0x01]
        self.this_area_count = bytearray(2)
        self.this_area_type = bytearray([area_type])
        self.index_match_size = bytearray([index_match_size])
        self.index_matchs = bytearray()
        self.index_data = bytearray()
        self.__index_data_size = index_data_size if area_type == 0x00 else 4
        self.__next_areas = []
    
    def __repr__(self):
        t = ""
        return t
    
    def add_next_area(self, match, area):
        assert self.this_area_type[0] == 0x01
        self.add_match(match, bytearray(4))
        self.__next_areas.append(area)

    def update_next_area_offset(self, init_base_offset=0):
        self_size = self.get_this_size()
        base_offset = init_base_offset + self_size
        if self.this_area_type[0] == 0x00:
            return base_offset
        count = int.from_bytes(self.this_area_count, 'big')
        assert count == len(self.__next_areas)
        data_size = self.__index_data_size
        for i in range(count):
            self.index_data[i*data_size: i*data_size + data_size] = base_offset.to_bytes(4, 'big')
            area = self.__next_areas[i]
            base_offset = area.update_next_area_offset(base_offset)
        assert base_offset - init_base_offset == len(self.get_data())
        return base_offset

    def add_or_update_match(self, match:bytearray, data:bytearray):
        if not self.update_match(match, data):
            self.add_match(match, data)

    def update_match(self, match:bytearray, data:bytearray):
        assert len(match) == self.index_match_size[0]
        assert len(data) == self.__index_data_size
        count = int.from_bytes(self.this_area_count, 'big')
        match_size = self.index_match_size[0]
        data_size = self.__index_data_size
        for i in range(count):
            mt = self.index_matchs[i*match_size: i*match_size + match_size]
            if mt == match:
                self.index_data[i*data_size: i*data_size + data_size] = data
                return True
        return False

    def add_match(self, match:bytearray, data:bytearray):
        assert len(match) == self.index_match_size[0]
        assert len(data) == self.__index_data_size
        self.index_matchs.extend(match)
        self.index_data.extend(data)
        count = int.from_bytes(self.this_area_count, 'big')
        count += 1
        assert count <= 0xFFFF
        self.this_area_count[:] = count.to_bytes(2, 'big')

    def get_this_size(self):
        return 2 + 1 + 1 + len(self.index_matchs) + len(self.index_data)

    def get_data(self):
        d = bytearray()
        d.extend(self.this_area_count)
        d.extend(self.this_area_type)
        d.extend(self.index_match_size)
        d.extend(self.index_matchs)
        d.extend(self.index_data)
        if self.this_area_type[0] == 0x01:
            for area in self.__next_areas:
                d.extend(area.get_data())
        return d

class CharData():
    def __init__(self, unicode, data):
        self.min_size = math.ceil(unicode.bit_length() / 8)
        self.unicode = unicode
        self.data = data
    
    def get_unicode_bytes(self, size=None):
        size = self.min_size if size == None else size
        assert self.min_size <= size
        return self.unicode.to_bytes(size, 'big')

def _make_index_area(char_data, unicode_max_size, match_byte_size=1, match_byte_pos=0):
    assert len(char_data) > 0
    char_data.sort(key=lambda cd: cd.unicode)
    if match_byte_size >= unicode_max_size - match_byte_pos:
        match_byte_size = unicode_max_size - match_byte_pos
        # remain byte
        data_size = len(char_data[0].data)
        this_area = IndexArea(0x00, match_byte_size, data_size)
        for cd in char_data:
            byte_id = cd.get_unicode_bytes(unicode_max_size)
            match = byte_id[match_byte_pos: match_byte_pos + match_byte_size]
            this_area.add_match(match, cd.data)
    else:
        this_area = IndexArea(0x01, match_byte_size, 4)
        # group char_data
        new_char_data_table = {}
        for cd in char_data:
            byte_id = cd.get_unicode_bytes(unicode_max_size)
            byte_id = int.from_bytes(byte_id[match_byte_pos: match_byte_pos + match_byte_size], 'big')
            if not byte_id in new_char_data_table:
                new_char_data_table[byte_id] = []
            new_char_data_list = new_char_data_table[byte_id]
            new_char_data_list.append(cd)
        # next_area
        new_pos = match_byte_pos + match_byte_size
        for match_id in new_char_data_table:
            new_char_data_ = new_char_data_table[match_id]
            match = match_id.to_bytes(match_byte_size, 'big')
            area = _make_index_area(new_char_data_, unicode_max_size, match_byte_size, new_pos)
            this_area.add_next_area(match, area)
    return this_area

def make_unicode_font(block_w, block_h, font_file, font_size, unicodes=list(c for c in range(32, 127)), position_offset=(0, 0), invert=False, ignore_bytes=[], output_path=None, preview_path=None, get_char_data=None):
    '''生成unicode点阵字体文件，自定义格式'''
    fnt = ImageFont.truetype(font_file, size=font_size)
    if get_char_data == None:
        get_char_data = _get_char_data
    unicodes.sort()
    # preview img
    preview = Image.new("1", (block_w*16, block_h*math.ceil(len(unicodes)/16)), color=255)
    preview_x_count = 0
    preview_y_count = 0
    used_unicode = []
    # make char data
    char_data = []
    count = 0
    for unic in unicodes:
        try:
            char = coding.UTF8.to_bytes(unic).decode("utf8")
        except:
            # print('error unic:', unic)
            continue
        buffer, fnt_img = get_char_data(char, block_w, block_h, fnt, position_offset, invert)
        count += 1
        print("{}/{}".format(count, len(unicodes)), end="\r")
        # filter
        # print(buffer)
        continue_flag = False
        for ignore_b in ignore_bytes:
            if callable(ignore_b):
                if ignore_b(char, buffer):
                    continue_flag = True
            else:
                if buffer == ignore_b:
                    continue_flag = True
        if continue_flag:
            continue
        # add char data
        char_data.append(CharData(unic, buffer))
        used_unicode.append(unic)
        # preview
        preview_pos = preview_x_count*block_w, preview_y_count*block_h
        preview.paste(fnt_img, preview_pos)
        preview_x_count += 1
        if preview_x_count >= 16:
            preview_x_count = 0
            preview_y_count += 1
    max_unicode_size = 0
    # find max unicode size
    for cd in char_data:
        if cd.min_size > max_unicode_size:
            max_unicode_size = cd.min_size
    # make fnt
    index_area = _make_index_area(char_data, max_unicode_size, 1)
    data = bytearray(b"u")
    data.extend(max_unicode_size.to_bytes(1, 'big'))
    data.extend(block_w.to_bytes(1, 'big'))
    data.extend(block_h.to_bytes(1, 'big'))
    index_area.update_next_area_offset(4)
    data.extend(index_area.get_data())
    print('data length:', len(data))
    # return
    if preview_path != None:
        preview.save(preview_path)
    if output_path != None:
        with open(output_path, "wb") as f:
            f.write(data)
    return data, preview, used_unicode

def main_unicode_16():
    block_width = 16
    block_height = 16
    font_path = os.path.join(current_path, "unifont-13.0.04.ttf")
    preview_path = os.path.join(current_path, "..", "out", "pix{}x{}.png".format(block_width, block_height))
    output_path = os.path.join(current_path, "..", "out", "pix{}x{}.ufnt".format(block_width, block_height))
    font_size = 16
    ignore_bytes = []
    unicodes = []
    unicodes.extend(c for c in range(0x20, 0x7E+1)) # ascii some
    unicodes.extend(c for c in range(0x2100, 0x21FF+1)) # symbols
    unicodes.extend(c for c in range(0x2200, 0x22FF+1)) # math symbols
    unicodes.extend(c for c in range(0x3000, 0x303F+1)) # cjk symbols and punctuation
    unicodes.extend(c for c in range(0x3040, 0x30FF+1)) # jp
    unicodes.extend(c for c in range(0x4E00, 0x9FFF+1)) # cjk general
    unicodes.extend(c for c in range(0xFF00, 0xFFEF+1)) # full ascii
    # make fnt
    backup_font_path = os.path.join(current_path, "文泉驿等宽微米黑.ttf")
    backup_fnt = ImageFont.truetype(backup_font_path, size=font_size)
    def should_ignore(char, buffer):
        frame = framebuf.FrameBuffer(buffer, block_width, block_height, framebuf.MONO_HLSB)
        filled = 0
        for x in range(block_width):
            for y in range(block_height):
                filled += frame.pixel(x, y)
        if filled >= block_width*block_height * 0.55:
            print("ignored:", char)
            return True
        return False
    ignore_bytes.append(should_ignore)
    def my_get_char_data(char_str, block_w, block_h, fnt, position_offset=(0, 0), invert=False):
        byts = char_str.encode("utf8")
        if len(byts) == 1 and byts[0] >= 0x20 and byts[0] <= 0x7E:
            # ascii use a different font
            return _get_char_data(char_str, block_w, block_h, backup_fnt, position_offset, invert)
        return _get_char_data(char_str, block_w, block_h, fnt, position_offset, invert)
    make_unicode_font(block_width, block_height, font_path, font_size, unicodes=unicodes, ignore_bytes=ignore_bytes, output_path=output_path, preview_path=preview_path, get_char_data=my_get_char_data)

def main_unicode_8():
    block_width = 8
    block_height = 8
    font_path = os.path.join(current_path, "DinkieBitmap-7pxDemo.ttf")
    preview_path = os.path.join(current_path, "..", "out", "pix{}x{}.png".format(block_width, block_height))
    output_path = os.path.join(current_path, "..", "out", "pix{}x{}.ufnt".format(block_width, block_height))
    font_size = 8
    ignore_bytes = []
    ignore_bytes.append(bytearray(8))
    ignore_bytes.append(bytearray(b'\xca\xac\xca\x00\xce\xee\xea\x00'))
    unicodes = []
    unicodes.extend(c for c in range(0x0000, 0xFFFF+1)) # full
    _, _, used_unicode = make_unicode_font(block_width, block_height, font_path, font_size, unicodes=unicodes, ignore_bytes=ignore_bytes, output_path=output_path, preview_path=preview_path)
    print("real font count:", len(used_unicode))
    print(used_unicode)

def main_unicode_10():
    block_width = 10
    block_height = 10
    font_path = os.path.join(current_path, "DinkieBitmap-9px.ttf")
    preview_path = os.path.join(current_path, "..", "out", "pix{}x{}.png".format(block_width, block_height))
    output_path = os.path.join(current_path, "..", "out", "pix{}x{}.ufnt".format(block_width, block_height))
    font_size = 10
    ignore_bytes = []
    ignore_bytes.append(bytearray(20))
    ignore_bytes.append(bytearray(b'\xe5\x00\x96\x00\x95\x00\xe4\x80\x00\x00\xc8\x80\xed\x80\xaa\x80\xc8\x80\x00\x00'))
    unicodes = []
    unicodes.extend(c for c in range(0x0000, 0xFFFF+1)) # full
    _, _, used_unicode = make_unicode_font(block_width, block_height, font_path, font_size, unicodes=unicodes, ignore_bytes=ignore_bytes, output_path=output_path, preview_path=preview_path)
    print("real font count:", len(used_unicode))
    # print(used_unicode)

if __name__ == "__main__":
    main_unicode_10()
    pass
