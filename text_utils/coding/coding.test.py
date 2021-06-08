try:
    from . import coding
except:
    import coding
from io import BytesIO

if __name__ == "__main__":
    # test utf16
    data = "你好龙龍\n不知道123".encode("utf16")
    stream = BytesIO(data)
    reader = coding.UTF16Reader(stream)
    assert reader.read() == [20320, 22909, 40857, 40845, 10, 19981, 30693, 36947, 49, 50, 51]
    for area,posi in coding.GB2312.all_available_pos():
        utf8 = coding.GB2312.to_bytes((area,posi)).decode("gb2312").encode("utf8")
        utf16 = coding.GB2312.to_bytes((area,posi)).decode("gb2312").encode("utf16")
        order = 'little' if utf16[:2] == b'\xff\xfe' else 'big'
        utf16 = utf16[2:]
        unicode = coding.UTF16.from_bytes(utf16, order)
        utf16_2 = coding.UTF16.to_bytes(unicode, order)
        try:
            assert utf16_2 == utf16
        except:
            print("utf16 test failed",area,posi,utf16,utf16_2,unicode)
            break
    # test utf8
    data = "你好龙龍\n不知道123".encode("utf8")
    stream = BytesIO(data)
    reader = coding.UTF8Reader(stream)
    assert reader.read() == [20320, 22909, 40857, 40845, 10, 19981, 30693, 36947, 49, 50, 51]
    for area,posi in coding.GB2312.all_available_pos():
        utf8 = coding.GB2312.to_bytes((area,posi)).decode("gb2312").encode("utf8")
        unicode = coding.UTF8.from_bytes(utf8)
        utf8_2 = coding.UTF8.to_bytes(unicode)
        try:
            assert utf8_2 == utf8
        except:
            print("utf8 test failed",area,posi,utf8,utf8_2,unicode)
            break
    # test gb2312
    poses = coding.GB2312.all_available_pos()
    # print(len(poses))
    for area,posi in poses:
        pos = coding.GB2312.to_dict_index((area,posi))
        area2, posi2 = coding.GB2312.from_dict_index(pos)
        try:
            assert area == area2
            assert posi == posi2
        except:
            print("gb2312 dict index test failed",area,posi,area2,posi2,pos)
            break
    ch = b"!"[0]
    while ch <= b"~"[0]:
        area, posi = coding.GB2312.from_ascii(ch)
        ch2 = coding.GB2312.to_ascii((area, posi))
        try:
            assert ch == ch2
            # print(bytes([ch]).decode("utf8"),end=" ")
            # print(gb2312.decode("gb2312"))
        except:
            print("gb2312 ascii convert test failed",ch,ch2)
            break
        ch = ch + 1
    pass
