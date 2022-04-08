"""
LZW ON THE MICRO CONTROLER
reference: http://giflib.sourceforge.net/whatsinagif/lzw_image_data.html
"""
import gc
try:
    from io import BytesIO
except:
    from uio import BytesIO

def _dump_bit(byte, size=8):
    return "{{:0{:d}b}}".format(size).format(byte)

def _dump_bytes(byts):
    lst = []
    for b in byts:
        lst.append(f"{b:08b}")
    return " ".join(lst)

def _pack_bit_stream(stream):
    return [stream, 0, 0]


def _read_bits(bit_stream_pack, read_bit_s=8):
    stream, last_bit_p, last_byte = bit_stream_pack
    value = 0
    remain_bit_s = read_bit_s
    while remain_bit_s > 0:
        if last_bit_p == 0:
            bts = stream.read(1)
            if (bts == None or len(bts) <= 0):
                bit_stream_pack[1] = last_bit_p
                bit_stream_pack[2] = 0
                return None # EOF
            last_byte = bts[0]
        tmp_s = min(remain_bit_s, 8-last_bit_p)
        mask = ~(0xFF << tmp_s)
        tmp_v = (last_byte & mask) & 0xFF
        value = value | (tmp_v << (read_bit_s - remain_bit_s))
        remain_bit_s -= tmp_s
        last_bit_p = (last_bit_p + tmp_s) % 8
        last_byte = last_byte >> tmp_s
    bit_stream_pack[1] = last_bit_p
    bit_stream_pack[2] = last_byte
    # print(f"reading {read_bit_s} bit with value {_dump_bit(value, read_bit_s)}")
    return value

def _write_bits(bit_stream_pack, value, write_bit_s=8):
    # print(f"writing {write_bit_s} bit with value {_dump_bit(value, write_bit_s)}")
    stream, last_bit_p, last_byte = bit_stream_pack
    remain_bit_s = write_bit_s
    while remain_bit_s > 0:
        if last_bit_p == 8:
            wlen = stream.write(bytes([last_byte]))
            if (wlen != 1):
                bit_stream_pack[1] = last_bit_p
                bit_stream_pack[2] = last_byte
                return write_bit_s - remain_bit_s
            last_bit_p = 0
            last_byte = 0
        tmp_s = min(remain_bit_s, 8-last_bit_p)
        mask = ~(0xFF << tmp_s)
        tmp_v = (value & mask) & 0xFF
        last_byte = last_byte | (tmp_v << last_bit_p)
        value = value >> tmp_s
        remain_bit_s -= tmp_s
        last_bit_p = last_bit_p + tmp_s
    bit_stream_pack[1] = last_bit_p
    bit_stream_pack[2] = last_byte

def _finish_write_bit(bit_stream_pack):
    stream, last_bit_p, last_byte = bit_stream_pack
    if last_bit_p <= 0:
        return 0
    wlen = stream.write(bytes([last_byte]))
    if wlen == 1:
        return last_bit_p
    else:
        return 0

def _pack_dict_item(pre, char):
    # pre_h, pre_low, char
    return bytes([(pre >> 8) & 0xFF, pre & 0xFF, char & 0xFF])

def _unpack_dict_item(byts):
    return (byts[0] << 8) | byts[1], byts[2]

class Encoder():
    def __init__(self, output_stream, init_dict_bit_length = 8, gif_mode = False):
        assert init_dict_bit_length <= 8 # support 8 bit max
        self._gfm = gif_mode
        self._rdw = 2 ** init_dict_bit_length # raw data within
        # self._rdw     : CODE CLEAR
        # self._rdw + 1 : CODE END
        self._nxc = self._rdw + (2 if gif_mode else 0) # next code (int)
        self._cbl = init_dict_bit_length + 1 # current bit length
        self._nia = 2 ** self._cbl # next increase (bit length) at
        self._bof = False # bit length overflow (12 bit)
        self._buf = -1 # index buffer, store last code
        self._dit = {} # bytes(3) -> int, map record to code
        self._out = _pack_bit_stream(output_stream)
    
    def close(self):
        """ YOU NEED TO CLOSE STREAM OBJECT BY YOURSELF """
        if self._buf >= 0:
            _write_bits(self._out, self._buf, self._cbl)
        if self._gfm:
            _write_bits(self._out, self._rdw+1, self._cbl)
        _finish_write_bit(self._out)

    def write1(self, value):
        _output = 0
        if self._buf < 0:
            if self._gfm:
                # output clear code before we start
                _write_bits(self._out, self._rdw, self._cbl)
            self._buf = value
        else:
            content = _pack_dict_item(self._buf, value)
            if content in self._dit:
                # found
                self._buf = self._dit[content]
            else:
                # not found
                _write_bits(self._out, self._buf, self._cbl)
                _output = self._buf
                self._buf = value
                if not self._bof:
                    # dict not overflow
                    self._dit[content] = self._nxc
                    # print(f"{self._nxc}: {_output} + {value}")
                    self._nxc += 1
                    # deal with bit length change
                    if self._nxc >= self._nia:
                        # print(f"bit change to {self._cbl + 1}")
                        self._cbl += 1
                        if self._cbl > 12:
                            self._cbl = 12
                            self._bof = True
                        self._nia = 2 ** self._cbl

    def write(self, data):
        for v in data:
            self.write1(v)
    
class Decoder():
    def __init__(self, input_stream, init_dict_bit_length = 8, temp_file=BytesIO()):
        assert init_dict_bit_length <= 8 # support 8 bit max
        self._gfm = False # auto 
        self._ibl = init_dict_bit_length
        self._rdw = 2 ** init_dict_bit_length # raw data within
        # self._rdw     : CODE CLEAR
        # self._rdw + 1 : CODE END
        self._dof = self._rdw # dict offset
        self._nxc = self._rdw # next code (int)
        self._cbl = init_dict_bit_length + 1 # current bit length
        self._nia = 2 ** self._cbl # next increase (bit length) at
        self._bof = False # bit length overflow (12 bit)
        self._buf = -1 # index buffer, store last code
        self._dit = temp_file # code(int) -> bytes(3)
        self._inp = _pack_bit_stream(input_stream)
        self._rgt = None # read generator
    
    def close(self):
        pass # no-op

    def _read_generator(self):
        while True:
            # data = []
            val = _read_bits(self._inp, self._cbl)
            if val == None:
                return
            if self._buf < 0:
                # auto set gif mode
                if val >= self._nxc:
                    self._gfm = True
                    self._dof = self._rdw + 2
                    self._nxc = self._rdw + 2
                if self._gfm and val == self._rdw:
                    val = _read_bits(self._inp, self._cbl) # read next code
                    if val == None: return
                self._buf = val
                # data.append(val)
                # yield from data
                yield val
                continue
            else:
                # gif mode special
                if self._gfm and val == self._rdw:
                    # clear dict
                    self._buf = -1
                    self._dof = self._rdw
                    self._nxc = self._rdw
                    self._cbl = self._ibl + 1
                    continue
                elif self._gfm and val == self._rdw + 1:
                    # end
                    return
                # 
                if val >= self._nxc:
                    # not in the code table
                    code = self._buf
                else:
                    code = val
                # search in code table
                if code < self._rdw:
                    # raw code
                    code_seq = [code]
                else:
                    # search value in code table
                    code_seq = []
                    search_code = code
                    while search_code >= self._rdw:
                        dict_offset = (search_code - self._dof) * 3
                        self._dit.seek(dict_offset)
                        search_code, code_val = _unpack_dict_item(self._dit.read(3))
                        # search_code, code_val = _unpack_dict_item(self._dit[dict_offset: dict_offset+3])
                        code_seq.append(code_val)
                    code_seq.append(search_code)
                    code_seq.reverse()
                if val >= self._nxc:
                    # not in the code table
                    code_seq.append(code_seq[0])
                # output code seq
                # data.extend(code_seq)
                # add to code table
                char = code_seq[0]
                if (not self._bof) or (self._nxc + 1 == self._nia):
                    # dict not overflow
                    self._dit.seek((self._nxc - self._dof) * 3)
                    self._dit.write(_pack_dict_item(self._buf, char))
                    # self._dit.extend(_pack_dict_item(self._buf, char))
                    # print(f"dict #{self._nxc}: {self._buf} + {char}") 
                    self._nxc += 1
                    # deal with bit length change
                    if self._nxc + 1 >= self._nia:
                        # print(f"bit change to {self._cbl + 1}")
                        self._cbl += 1
                        if self._cbl > 12:
                            self._cbl = 12
                            self._bof = True
                        self._nia = 2 ** self._cbl
                self._buf = val
                yield from code_seq

    def read1(self):
        if self._rgt == None:
            self._rgt = self._read_generator()
        try:
            return next(self._rgt)
        except StopIteration:
            return None
    
    def read(self, count=-1):
        if count < 0:
            return bytes(self._rgt if self._rgt != None else self._read_generator())
        else:
            ba = bytearray()
            while count > 0:
                v = self.read1()
                if v == None:
                    return bytes(ba)
                ba.append(v)
                count -= 1
            return bytes(ba)
