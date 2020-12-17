import sys, os

import PIL
current_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(current_path, "..", "text_utils", "coding"))
sys.path.append(os.path.join(current_path, "utils"))
sys.path.append(os.path.join(current_path, "ssd1306desktop"))

from PIL import Image, ImageFont, ImageDraw
import math
import coding, framebuf

def make_gb2312_font(block_w, block_h, font_file, font_size, init_data=None, init_preview=None, area=None, position_offset=(0,0), invert=False, ignore_bytes=[], output_path=None, preview_path=None):
    fnt = ImageFont.truetype(font_file, size=font_size)
    # 预览图片, 区块10x10, 94区
    preview = Image.new("1", (block_w*10, block_h*10*87), color=255) if init_preview == None else init_preview
    preview_draw = ImageDraw.Draw(preview)
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
            fnt_img = Image.new("1", (block_w, block_h), color=255)
            fnt_draw = ImageDraw.Draw(fnt_img)
            fnt_draw.text(position_offset, char_str, fill=0, font=fnt, anchor="lt", spacing=0)
            # draw framebuffer
            buffer = bytearray(block_size)
            frame = framebuf.FrameBuffer(buffer, block_w, block_h, framebuf.MONO_HLSB)
            for x in range(block_w):
                for y in range(block_h):
                    pixel = fnt_img.getpixel((x, y))
                    pixel = 1 if (pixel == 0) ^ invert else 0
                    frame.pixel(x, y, pixel)
            continue_flag = False
            for ignore_b in ignore_bytes:
                if buffer == ignore_b:
                    continue_flag = True
            if continue_flag:
                continue
            # update preview
            preview_pos = ((p%10)*block_w + position_offset[0], (a*10*block_h) + (p//10)*block_h + position_offset[1])
            preview_draw.text(preview_pos, char_str, fill=0, font=fnt, anchor="lt", spacing=0)
            # write data
            offset = coding.GB2312.to_dict_index(char) * block_size
            data[offset:offset+block_size] = buffer
            print(char_str, offset)
            # break
    if preview_path != None:
        preview.save(preview_path)
    if output_path != None:
        with open(output_path, "wb") as f:
            f.write(data)
    return data, preview

def test():
    pass

if __name__ == "__main__":
    # config fount
    block_width = 8
    block_height = 8
    preview_path = os.path.join(current_path, "out", "pix{}x{}.png".format(block_width, block_height))
    output_path = os.path.join(current_path, "out", "pix{}x{}.fnt".format(block_width, block_height))
    # make font
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