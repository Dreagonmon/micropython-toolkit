''' 生成自定义格式的unicode点阵字体
FILE:
[font_width: 1B][font_height: 1B]
[area_index: 256 * [block_offset: 2B][block_size: 1B]] # area_index[0] is 'number of block', because 0x00 always start at offset 0
[[pos_index: 1B]*'number of block'... [font_data: font_data_size]*'number of block'...]... # (font_data_size + 1) * 'number of block'
unicode序号大端编码，得到两byte，第一byte为pos_index，第二byte为area_index
'''
import sys, os
from typing import List, Tuple

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
    char_area = list() # type: List[List[Tuple[int, bytearray]]]
    for _ in range(256):
        char_area.append(list())
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
        if int.bit_length(unic) > 16: # must small than 2 byte
            continue_flag = True
        if continue_flag:
            continue
        # add char data
        unic_bytes = int.to_bytes(unic, 2, 'big')
        pos_index = unic_bytes[0]
        area_index = unic_bytes[1]
        char_area[area_index].append((pos_index, buffer))
        # preview
        preview_pos = preview_x_count*block_w, preview_y_count*block_h
        preview.paste(fnt_img, preview_pos)
        preview_x_count += 1
        if preview_x_count >= 16:
            preview_x_count = 0
            preview_y_count += 1
        used_unicode.append(unic)
    # make font
    head = bytearray()
    head.extend(block_w.to_bytes(1, 'big'))
    head.extend(block_h.to_bytes(1, 'big'))
    body = bytearray()
    number_of_block = int.to_bytes(len(used_unicode), 2, 'big')
    count = 0
    for i in range(256):
        chars_in_area = char_area[i]
        chars_in_area.sort(key=lambda v: v[0])
        # update area index
        offset = int.to_bytes(count, 2, 'big')
        block_size = int.to_bytes(len(chars_in_area), 1, 'big')
        if i == 0:
            head.extend(number_of_block)
        else:
            head.extend(offset)
        head.extend(block_size)
        # update area_data
        pos_index = bytearray()
        pos_data = bytearray()
        for info in chars_in_area:
            pos_index.append(info[0])
            pos_data.extend(info[1])
        body.extend(pos_index)
        body.extend(pos_data)
        #
        count += len(chars_in_area)

    data = bytearray()
    data.extend(head)
    data.extend(body)
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
    # unicodes.extend(c for c in range(0x0000, 0xFFFF+1)) # full
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
    font_path = os.path.join(current_path, "dinkie-bitmap-7px.ttf")
    preview_path = os.path.join(current_path, "..", "out", "pix{}x{}.png".format(block_width, block_height))
    output_path = os.path.join(current_path, "..", "out", "pix{}x{}.ufnt".format(block_width, block_height))
    font_size = 8
    ignore_bytes = []
    ignore_bytes.append(bytearray(8))
    ignore_bytes.append(bytearray(b'\xca\xac\xca\x00\xce\xee\xea\x00'))
    unicodes = []
    # unicodes.extend(c for c in range(0x20, 0x7E+1)) # ascii some
    unicodes.extend(c for c in range(0x0000, 0xFFFF+1)) # full
    _, _, used_unicode = make_unicode_font(block_width, block_height, font_path, font_size, unicodes=unicodes, ignore_bytes=ignore_bytes, output_path=output_path, preview_path=preview_path)
    print("real font count:", len(used_unicode))
    # print(used_unicode)

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
    # unicodes.extend(c for c in range(0x20, 0x7E+1)) # ascii some
    unicodes.extend(c for c in range(0x0000, 0xFFFF+1)) # full
    _, _, used_unicode = make_unicode_font(block_width, block_height, font_path, font_size, unicodes=unicodes, ignore_bytes=ignore_bytes, output_path=output_path, preview_path=preview_path)
    print("real font count:", len(used_unicode))
    # print(used_unicode)

if __name__ == "__main__":
    main_unicode_8()
    main_unicode_10()
    main_unicode_16()
    pass
