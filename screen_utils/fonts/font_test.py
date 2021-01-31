import sys, os

current_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(current_path, "..", "..", "text_utils", "coding"))
sys.path.append(os.path.join(current_path, "..", "ssd1306desktop"))
sys.path.append(os.path.join(current_path, "..", "utils"))

import framebuf, ubmfont

if __name__ == "__main__":
    print('> test start <')
    fp = os.path.join(current_path, "..", "out", "pix8x8.ufnt")
    f = open(fp, 'rb')
    fd = ubmfont.FontDrawUnicode(f)
    print("font size:", fd.get_font_size())
    frame = framebuf.FrameBuffer(bytearray(32*16//8), 32, 16, framebuf.MONO_VLSB)
    frame.fill(1)
    fd.draw_on_frame('你好啊幻龙\n尘世幻龙', frame, 0, 0, 0, 32)
    print(frame)
