def ch_sym(value):
    tab = {
65292:44, # ，
12290:46, # 。
65306:58, # ：
65307:59, # ；
8220:34, # “
8221:34, # ”
8216:39, # ‘
8217:39, # ’
12304:91, # 【
12305:93, # 】
9632:43, # ■
8251:43, # ※
65288:40, # （
65289:41, # ）
12298:60, # 《
12299:62, # 》
8230:46, # …
65509:36, # ￥
12289:44, # 、
8212:45, # —
    }
    if value in tab:
        return tab[value]
    else:
        return value

def u8len(first_byte):
    pat = 0x01 << 7 # 1000000
    byt = first_byte # first byte
    l = 0 # length
    while byt & pat != 0:
        l = l + 1
        pat = pat >> 1
    if l == 0:
        l = 1 # for ascii
    return l

def int2bytes(value):
    byts = []
    if value == 0:
        byts.append(0)
    while value > 0:
        b = value & 0xFF
        byts.append(b)
        value = value >> 8
    byts.reverse()
    return bytearray(byts)

def u82int(u8):
    l = u8len(u8)
    value = 0x00
    if l == 1:
        value = value + u8[0]
    else:
        # head
        pat = 0xFF >> (l+1)
        value = value | (u8[0]&pat) # head byte
        for i in range(1,l):
            value = value << 6
            value = value | (u8[i]&0x3F) # following byte
    return value

def bytes2int(byts):
    value = 0x00
    for b in byts:
        value = value << 8
        value = value | b
    return value


def int2u8(value):
    u8 = None
    if value <= 0x7F:
        # 1 byte utf-8
        u8 = bytearray([value])
        pass
    elif value <= 0x07FF:
        # 2 bytes utf-8
        u8 = bytearray([0]*2)
        u8[0] = 0xC0 # 110 xxxxx
        u8[0] = u8[0] | (value >> 6) # xxxxx|
        u8[1] = 0x80 # 10 xxxxxx
        u8[1] = u8[1] | (value & 0x3F) # 00000 xxxxxx
        pass
    elif value <= 0xFFFF:
        # 3 bytes utf-8
        u8 = bytearray([0]*3)
        u8[0] = 0xE0 # 1110 xxxx
        u8[0] = u8[0] | (value >> 12) # xxxx|
        u8[1] = 0x80 # 10 xxxxxx
        u8[1] = u8[1] | ((value>>6) & 0x3F) # 0000 xxxxxx 000000
        u8[2] = 0x80 # 10 xxxxxx
        u8[2] = u8[2] | (value & 0x3F) # 0000 000000 xxxxxx
        pass
    elif value <= 0x1FFFF:
        # 4 bytes utf-8
        u8 = bytearray([0]*4)
        u8[0] = 0xF0 # 11110 xxx
        u8[0] = u8[0] | (value >> 18) # xxx|
        u8[1] = 0x80 # 10 xxxxxx
        u8[1] = u8[1] | ((value>>12) & 0x3F) # 000 xxxxxx 000000 000000
        u8[2] = 0x80 # 10 xxxxxx
        u8[2] = u8[2] | ((value>>6) & 0x3F) # 000 000000 xxxxxx 000000
        u8[3] = 0x80 # 10 xxxxxx
        u8[3] = u8[3] | (value & 0x3F) # 000 000000 000000 xxxxxx
        pass
    elif value <= 0x7FFFFFF:
        # 5 bytes utf-8
        u8 = bytearray([0]*5)
        u8[0] = 0xF8 # 111110 xx
        u8[0] = u8[0] | (value >> 24) # xx|
        u8[1] = 0x80 # 10 xxxxxx
        u8[1] = u8[1] | ((value>>18) & 0x3F) # 000 xxxxxx 000000 000000 000000
        u8[2] = 0x80 # 10 xxxxxx
        u8[2] = u8[2] | ((value>>12) & 0x3F) # 000 000000 xxxxxx 000000 000000
        u8[3] = 0x80 # 10 xxxxxx
        u8[3] = u8[3] | ((value>>6) & 0x3F) # 000 000000 000000 xxxxxx 000000
        u8[4] = 0x80 # 10 xxxxxx
        u8[4] = u8[4] | (value & 0x3F) # 000 000000 000000 000000 xxxxxx
        pass
    elif value <= 0x7FFFFFF:
        # 6 bytes utf-8
        u8 = bytearray([0]*6)
        u8[0] = 0xFC # 1111110 x
        u8[0] = u8[0] | (value >> 30) # x|
        u8[1] = 0x80 # 10 xxxxxx
        u8[1] = u8[1] | ((value>>24) & 0x3F) # 000 xxxxxx 000000 000000 000000 000000
        u8[2] = 0x80 # 10 xxxxxx
        u8[2] = u8[2] | ((value>>18) & 0x3F) # 000 000000 xxxxxx 000000 000000 000000
        u8[3] = 0x80 # 10 xxxxxx
        u8[3] = u8[3] | ((value>>12) & 0x3F) # 000 000000 000000 xxxxxx 000000 000000
        u8[4] = 0x80 # 10 xxxxxx
        u8[4] = u8[4] | ((value>>6) & 0x3F) # 000 000000 000000 000000 xxxxxx 000000
        u8[5] = 0x80 # 10 xxxxxx
        u8[5] = u8[5] | (value & 0x3F) # 000 000000 000000 000000 000000 xxxxxx
        pass
    else:
        # and more ...
        pass
    return u8

def url_decode(url):
    pos = 0
    byts = b''
    while pos < len(url):
        ch = url[pos]
        if ch != '%':
            # ascii code
            byts = byts+ch.encode('utf-8')
            pos = pos + 1
            continue
        else :
            # no ascii code
            hex = url[pos+1:pos+3]
            byts = byts + bytes([int(hex,16)])
            pos = pos + 3
            continue
    return byts.decode('utf-8')
