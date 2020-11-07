import coding
from io import BytesIO
SPACE_CHAR = b'\xa1\xa1'
class Codecs(object):
    def __init__(self, dict_fp):
        self.__dict_fp = dict_fp
        # read header
        self.__index_table = []
        for _ in range(256):
            self.__index_table.append(int.from_bytes(self.__dict_fp.read(2), 'big'))
    def from_unicode(self, unicode):
        if (unicode < 127):
            # ascii byte
            return bytes([unicode])
        unicode = unicode.to_bytes(2, 'big')
        char_id = unicode[0]
        section = unicode[1]
        start_index = 0 if section <= 0 else self.__index_table[section-1]
        end_index = self.__index_table[section]
        section_size = end_index - start_index
        self.__dict_fp.seek(start_index*3+512)
        for _ in range(section_size):
            data = self.__dict_fp.read(3)
            if char_id == data[0]:
                return data[1:3]
        return SPACE_CHAR
    def from_stream(self, stream, limit=-1):
        count = 0
        resault = bytearray()
        reader = coding.UTF8Reader(stream)
        for u in reader.chars():
            resault.extend(self.from_unicode(u))
            count += 1
            if limit > 0 and count >= limit:
                return resault
        return resault
    def from_string(self, string):
        stream = BytesIO(string.encode("utf8"))
        return self.from_stream(stream)
