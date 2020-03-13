from text_utils import coding

if __name__ == "__main__":
    poses = coding.GB2312.all_available_pos()
    print(len(poses))
    for area,posi in poses:
        pos = coding.GB2312.pos2available_pos(area,posi)
        area2, posi2 = coding.GB2312.available_pos2pos(pos)
        try:
            assert area == area2
            assert posi == posi2
        except:
            print("test failed",area,posi,area2,posi2,pos)
            break
    ch = b"!"[0]
    while ch <= b"~"[0]:
        gb2312 = coding.GB2312.ascii2gb2312(ch)
        ch2 = coding.GB2312.gb23122ascii(gb2312)
        try:
            assert ch == ch2
            # print(bytes([ch]).decode("utf8"),end=" ")
            # print(gb2312.decode("gb2312"))
        except:
            print("test failed",ch,ch2,gb2312)
            break
        ch = ch + 1
    pass