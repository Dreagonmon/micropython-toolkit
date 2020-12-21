''' use unicode bitmap font (custom defined format) '''
WINCE_START_OF_FILE = 0
WINCE_CURRENT = 1
WINCE_END_OF_FILE = 2

def _binary_search_bytes(lis, target, block_size=1):
    left = 0
    right = len(lis) - 1
    while left <= right:
        mid = (left + right) // 2 //block_size
        mid_byts = lis[mid*block_size: mid*block_size+block_size]
        eq = 0
        for i in range(block_size):
            b1 = mid_byts[i]
            t = target[i]
            if b1 == t:
                continue
            elif t < b1:
                eq = -1
                break
            else:
                eq = 1
                break
        if eq < 0:
            right = mid - block_size
        elif eq > 0:
            left = mid + block_size
        else:
            return mid
    return -1  # not found

class FontQuery():
    def __init__(self, stream):
        tmp_data = stream.read(4)
        self.__stream = stream
        assert tmp_data[0:1] == b'u'
        self.__max_unicode_size = tmp_data[1]
        self.__font_width = tmp_data[2]
        self.__font_height = tmp_data[3]
        w = self.__font_width // 8
        w += 0 if self.__font_width % 8 == 0 else 1
        self.__font_block_size = self.__font_height * w
    
    def __repr__(self):
        return '<FontQuery width="{}" height="{}" blocksize="{}" unicodelength="{}"/>'.format(self.__font_width, self.__font_height, self.__font_block_size, self.__max_unicode_size)

    def query(self, unicode, match_pos=0, offset=4):
        self.__stream.seek(offset, WINCE_START_OF_FILE)
        tmp_data = self.__stream.read(4)
        offset += 4
        this_area_count = int.from_bytes(tmp_data[0: 2], 'big')
        this_area_type = tmp_data[2]
        index_match_size = tmp_data[3]
        del tmp_data
        if this_area_type == 0x00 and (index_match_size != self.__max_unicode_size - match_pos):
            return None # can`t find font
        # parse match target and list
        match_target_byts = unicode.to_bytes(self.__max_unicode_size, 'big')[match_pos: match_pos + index_match_size]
        matchs_index_byts = self.__stream.read(index_match_size * this_area_count)
        offset += index_match_size * this_area_count
        # find match
        index = _binary_search_bytes(matchs_index_byts, match_target_byts, index_match_size) // index_match_size
        if index < 0:
            return None
        # process resault
        if this_area_type == 0x00:
            target_offset = offset + self.__font_block_size * index
            self.__stream.seek(target_offset, WINCE_START_OF_FILE)
            return bytearray(self.__stream.read(self.__font_block_size))
        else:
            # next area
            target_offset = offset + 4 * index
            self.__stream.seek(target_offset, WINCE_START_OF_FILE)
            jump_offset = int.from_bytes(self.__stream.read(4), 'big')
            return self.query(unicode, match_pos+index_match_size, jump_offset)
        
    def get_font_size(self):
        return self.__font_width, self.__font_height
