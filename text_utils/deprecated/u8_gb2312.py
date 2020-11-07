'''
基于btree的unicode to gb2312编码转换工具
import u8_gb2312
u8_gb2312.init("unicode2gb2312.btree")
u8_gb2312.convert_u8_gb2312("你好")
u8_gb2312.convert_u8_gb2312("你好".encode())
'''
try:
    from . import coding
except:
    import coding
import btree

__dbf = None
__db = None
def init(btree_file):
    global __dbf, __db
    if __dbf == None or __db == None:
        __dbf = open(btree_file,"rb")
        __db = btree.open(__dbf)

def deinit():
    global __dbf, __db
    __db.close()
    __dbf.close()

def __convert(unic):
    global __db
    try:
        key = unic.to_bytes(2,'big')
        return __db[key]
    except:
        return False

def convert_u8_gb2312(byts):
    if type(byts) == str:
        byts = byts.encode()
    index = 0
    res = bytearray()
    while index < len(byts):
        fb = byts[index]
        l = coding.UTF8.byte_size(fb)
        if l == 1:
            index += 1
            res.extend(coding.GB2312.to_bytes(coding.GB2312.from_ascii(fb)))
            continue
        unic = coding.UTF8.from_bytes(byts[index:index+l])
        bs = __convert(unic)
        if not bs:
            index += l
            res.extend(coding.GB2312.to_bytes(coding.GB2312.from_ascii(32)))
            continue
        res.extend(bs)
        index += l
    return res