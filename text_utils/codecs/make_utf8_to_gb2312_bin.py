# 所有的GB2312汉字的UNICODE编码都是两字节
# micropython本身支持utf8编码的字符串，转成GB2312只是为了方便使用字库绘制汉字
# 数字和unicode统一无符号大端编码
# [second_byte index table] # 256 * 2 bytes, index info. table[0] means *,0x01`s index, table[255] is number_of_block
# [[unicode_first_byte][gb2312_two_bytes]]... # number_of_block * 3 bytes block.
# 用unicode数字的低8位作为区域码，分布更加均匀
import sys, os
current_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(current_path, "..", "coding"))

import coding

if __name__ == "__main__":
    ch_dict = {}
    # 添加GB2312字符
    poses = coding.GB2312.all_available_pos()
    for pose in poses:
        gb2312 = coding.GB2312.to_bytes(pose)
        # 过滤无效字符
        try:
            utf8 = gb2312.decode("gb2312").encode("utf8")
            # utf8还原成UNICODE
            unicode = coding.UTF8.from_bytes(utf8)
            assert unicode.bit_length() <= 16
            unicode = unicode.to_bytes(2,"big",signed=False)
            ch_dict[int.from_bytes(unicode, 'little')] = (unicode, gb2312)
        except:
            print("(",gb2312[0],",",gb2312[1],"),")
    # 添加ASCII字符
    # for ascii in range(b"!"[0], b"~"[0]+1):
    #     gb2312 = coding.GB2312.to_bytes(coding.GB2312.from_ascii(ascii))
    #     unicode = ascii.to_bytes(2,"big",signed=False)
    #     ch_dict[int.from_bytes(unicode, 'little')] = (unicode, gb2312)
    # 按照第二字节优先从小到大排序
    keys = list(ch_dict.keys())
    keys.sort()
    # 制作字典
    section_size_table = [0] * 256
    body = bytearray()
    print("共有字符{}个".format(len(keys)))
    assert len(keys) > 0
    for k in keys:
        unicode, gb2312 = ch_dict[k]
        second_byte = unicode[1]
        section_size_table[second_byte] += 1
        # 3 bytes
        body.append(unicode[0])
        body.extend(gb2312)
    header = bytearray()
    index = 0
    i=0
    for section_count in section_size_table:
        index += section_count
        i += 1
        header.extend(index.to_bytes(2, 'big', signed=False))
    assert int.from_bytes(header[-2:], 'big') == len(keys)
    # 写入字典
    with open("codecs_utf8_gb2312.bin", "wb") as f:
        count = 0
        count += f.write(header)
        count += f.write(body)
        print("编码字典大小: {} bytes".format(count))