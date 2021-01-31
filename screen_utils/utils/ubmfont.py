from bmfont import FontDraw, _draw_char_one_by_one

def _area_pos_from_char(char):
    u8 = char.encode('utf-8')
    l = len(u8)
    # unicode value
    value = 0x00
    if l == 1:
        value = value + u8[0]
    else:
        # head
        pat = 0xFF >> (l+1)
        value = value | (u8[0] & pat)  # head byte
        for i in range(1, l):
            value = value << 6
            value = value | (u8[i] & 0x3F)  # following byte
    # area and pos
    unic_bytes = int.to_bytes(value, 2, 'big')
    return unic_bytes[1], unic_bytes[0] # area, pos

def _unicode_is_special_char(char, ascii):
    return char.encode("utf8")[0] == ascii

def _draw_unicode_on_frame(frame, font_width, font_data, x, y, color):
    if font_data != None:
        xp = x
        yp = y
        end_x = x + font_width
        for hdata in font_data:
            for bit in range(8):
                pat = 0b10000000 >> bit
                if (hdata & pat) != 0:
                    if 0 <= xp and 0 <= yp:
                        frame.pixel(xp, yp, color)
                xp += 1
            if xp >= end_x:
                xp = x
                yp += 1

BASE_OFFSET = 2 + (256 * 3)
class FontDrawUnicode(FontDraw):
    def __init__(self, font_stream):
        self.__font_file = font_stream
        self.__area_offset = []
        self.__area_size = bytearray()
        self.__font_count = 0
        self.__font_width = self.__font_file.read(1)[0]
        self.__font_height = self.__font_file.read(1)[0]
        w_block = self.__font_width // 8
        w_block += 0 if self.__font_width % 8 == 0 else 1
        self.__font_data_size = w_block * self.__font_height
        for i in range(256):
            offset = int.from_bytes(self.__font_file.read(2), 'big')
            size = int.from_bytes(self.__font_file.read(1), 'big')
            if i == 0:
                self.__font_count = offset
                self.__area_offset.append(0)
            else:
                self.__area_offset.append(offset)
            self.__area_size.append(size)
    
    def __get_char_data(self, area, pos):
        offset = (self.__area_offset[area] * (self.__font_data_size + 1)) + BASE_OFFSET
        size = self.__area_size[area]
        self.__font_file.seek(offset)
        pos_lst = list(self.__font_file.read(size))
        try:
            data_index = pos_lst.index(pos)
            offset += size + self.__font_data_size * data_index
            self.__font_file.seek(offset)
            return bytearray(self.__font_file.read(self.__font_data_size))
        except:
            return None # not found

    def _unicode_draw_char_on(self, char, frame, x, y, color):
        area, pos = _area_pos_from_char(char)
        data = self.__get_char_data(area, pos)
        _draw_unicode_on_frame(frame, self.__font_width, data, x, y, color)

    def get_font_size(self):
        return (self.__font_width, self.__font_height)
    
    def draw_on_frame(self, text, frame, x, y, color=1, width_limit=-1, height_limit=-1):
        return _draw_char_one_by_one(frame, x, y, color, width_limit, height_limit, (self.__font_width, self.__font_height), text, _unicode_is_special_char, self._unicode_draw_char_on)
