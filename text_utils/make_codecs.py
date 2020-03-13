'''
编码转换辅助文件，文件开头：|2 b"CO"|4记录的编码数量，即 文件大小=数量*(源长度+目标长度)+8|1源长度|1目标长度|
之后 |源编码|目标编码| 为一组，按照源编码从小到大排列，使用时二分搜索查找对应的编码转换
'''
import coding
def main():
    # unicode to gb2312
    body_data = bytearray()
    ch_dict = {}
    poses = coding.GB2312.all_available_pos()
    for area, posi in poses:
        byts = coding.GB2312.pos2gb2312(area,posi)
        # 过滤无效字符
        try:
            utf8 = byts.decode("gb2312").encode("utf8")
        except:
            print("(",area,",",posi,"),")
            utf8 = b" "
        # utf8还原成UNICODE
        unicode = coding.UTF_8.u82unicode(utf8)
        ch_dict[unicode] = byts
    # 从小到大排序
    keys = list(ch_dict.keys())
    keys.sort()
    # 统一无符号大端编码，大小也是这么比较的
    for unicode in keys:
        body_data.extend(unicode.to_bytes(2,"big",signed=False))
        body_data.extend(ch_dict[unicode])
        print("0x{:X}".format(unicode),"0x{:X}".format(int.from_bytes(ch_dict[unicode],"big",signed=False)))
    print(len(body_data))
    count = len(body_data) // 4
    header_data = bytearray(b"CO")
    header_data.extend(count.to_bytes(4,"big",signed=False))
    header_data.extend((2).to_bytes(1,"big",signed=False))
    header_data.extend((2).to_bytes(1,"big",signed=False))
    with open("unicode2gb2312.codec","wb") as f:
        f.write(header_data)
        f.write(body_data)

if __name__ == "__main__":
    main()