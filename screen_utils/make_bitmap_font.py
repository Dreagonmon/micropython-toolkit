import sys, os

current_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(current_path, "..", "text_utils", "coding"))
sys.path.append(os.path.join(current_path, "utils"))
sys.path.append(os.path.join(current_path, "ssd1306desktop"))

from PIL import Image, ImageFont, ImageDraw
import math
import coding, framebuf

def _get_char_data(char_str, block_w, block_h, fnt, position_offset, invert):
    block_size = math.ceil(block_w / 8) * block_h
    char_left, char_top, char_right, char_bottom = fnt.getbbox(char_str)
    char_width = char_right - char_left
    char_height = char_bottom - char_top
    char_x_offset = (block_w - char_width) // 2
    # char align to center bottom
    if char_bottom <= block_h - 1:
        char_y_offset = char_top
    elif char_height >= block_h * 0.8:
        # simplely remove top margin
        char_y_offset = 0
    else:
        char_y_offset = block_h - 1 - char_height
    char_offset = (position_offset[0] + char_x_offset, position_offset[1] + char_y_offset)
    # draw char
    fnt_img = Image.new("1", (block_w, block_h), color=255)
    fnt_draw = ImageDraw.Draw(fnt_img)
    fnt_draw.text(char_offset, char_str, fill=0, font=fnt, anchor="lt", spacing=0)
    # draw framebuffer
    buffer = bytearray(block_size)
    frame = framebuf.FrameBuffer(buffer, block_w, block_h, framebuf.MONO_HLSB)
    for x in range(block_w):
        for y in range(block_h):
            pixel = fnt_img.getpixel((x, y))
            pixel = 1 if (pixel == 0) ^ invert else 0
            frame.pixel(x, y, pixel)
    return buffer, fnt_img

def make_gb2312_font(block_w, block_h, font_file, font_size, init_data=None, init_preview=None, area=None, position_offset=(0,0), invert=False, ignore_bytes=[], output_path=None, preview_path=None):
    fnt = ImageFont.truetype(font_file, size=font_size)
    # 预览图片, 区块10x10, 1~87区
    preview = Image.new("1", (block_w*10, block_h*10*87), color=255) if init_preview == None else init_preview
    # gb2312区位码
    AREA = range(87) if area == None else area
    POS = range(94)
    data = bytearray(math.ceil(block_w / 8) * block_h * 87 * 94) if init_data == None else bytearray(init_data)
    block_size = math.ceil(block_w / 8) * block_h
    for a in AREA:
        for p in POS:
            char = (a+1, p+1)
            if coding.GB2312.is_unavailable_pos(char):
                continue
            char_str = coding.GB2312.to_bytes(char).decode("gb2312")
            # draw char
            buffer, fnt_img = _get_char_data(char_str, block_w, block_h, fnt, position_offset, invert)
            # filter
            continue_flag = False
            for ignore_b in ignore_bytes:
                if buffer == ignore_b:
                    continue_flag = True
            if continue_flag:
                continue
            # update preview
            preview_pos = ((p%10)*block_w, (a*10*block_h) + (p//10)*block_h)
            preview.paste(fnt_img, preview_pos)
            # write data
            offset = coding.GB2312.to_dict_index(char) * block_size
            data[offset:offset+block_size] = buffer
            # print(char_str, offset)
            # break
    if preview_path != None:
        preview.save(preview_path)
    if output_path != None:
        with open(output_path, "wb") as f:
            f.write(data)
    return data, preview

if __name__ == "__main__":
    # config fount 16px
    block_width = 16
    block_height = 16
    preview_path = os.path.join(current_path, "out", "pix{}x{}.png".format(block_width, block_height))
    output_path = os.path.join(current_path, "out", "pix{}x{}.fnt".format(block_width, block_height))
    font_path = os.path.join(current_path, "fonts", "unifont-13.0.04.ttf")
    ignore_bytes = []
    font_size = 16
    data, preview = make_gb2312_font(block_width, block_height, font_path, font_size, ignore_bytes=ignore_bytes, output_path=output_path, preview_path=preview_path)

    # config fount 8px
    block_width = 8
    block_height = 8
    preview_path = os.path.join(current_path, "out", "pix{}x{}.png".format(block_width, block_height))
    output_path = os.path.join(current_path, "out", "pix{}x{}.fnt".format(block_width, block_height))
    # stage 1
    font_path = os.path.join(current_path, "fonts", "文泉驿等宽微米黑.ttf")
    ignore_bytes = []
    font_size = 8
    data, preview = make_gb2312_font(block_width, block_height, font_path, font_size, ignore_bytes=ignore_bytes, output_path=output_path, preview_path=preview_path)
    # stage 2
    font_path = os.path.join(current_path, "fonts", "DinkieBitmap-7pxDemo.ttf") # ignore b'\xca\xac\xca\x00\xce\xee\xea\x00'
    ignore_bytes = [b'\xca\xac\xca\x00\xce\xee\xea\x00']
    font_size = 8
    data = make_gb2312_font(block_width, block_height, font_path, font_size,
        init_data=data, init_preview=preview,
        ignore_bytes=ignore_bytes, output_path=output_path, preview_path=preview_path)
    pass