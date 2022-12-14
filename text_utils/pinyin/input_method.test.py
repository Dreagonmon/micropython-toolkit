try:
    from .input_method import InputMethod
except:
    from input_method import InputMethod

def __show(txt:str,input_s:str,words:str):
    import os
    clear = "\n" * os.get_terminal_size()[1]
    print(clear)
    print(txt)
    print(words)
    print(input_s)
    # text = "\r{:<16} {:<16} {:<64}".format(txt,input_s,words)
    # print(text,end="")

def __test(dict_fp):
    try:
        import msvcrt
        getch = msvcrt.getch
    except:
        import termios, sys
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        new = termios.tcgetattr(fd)
        # turn off echo and press-enter
        new[3] = new[3] & ~termios.ECHO & ~termios.ICANON
        def getch():
            try:
                termios.tcsetattr(fd, termios.TCSADRAIN, new)
                while True:
                    char = sys.stdin.read(1)
                    return char.encode("ascii")
            finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old)
    c = getch()
    input_manager = InputMethod(dict_fp)
    print("小写字母输入拼音，`[`重置候选词分页，`]`下一页候选词，数字键选择候选词，Ctrl+C`退出")
    txt = "" # 已输入文字
    words = [] # 缓存的候选词列表
    while c != b'\x03':
        # b'\x08' backspace
        # b'\x03' ctrl+c
        # print("0x{:02X}".format(c[0]))
        # 换行
        if c == b'\r':
            print("\r{}".format(txt))
            txt = ""
            words = []
            input_manager.clear()
        # 候选词翻页事件
        if c[0] == 0x5B:
            input_manager.reset_word()
            words = input_manager.some_word(5)
        if c[0] == 0x5D:
            words = input_manager.some_word(5)
            if len(words)==0:
                input_manager.reset_word()
                words = input_manager.some_word(5)
        # 选择候选词事件
        if c[0] > 0x30 and c[0] < 0x36:
            index = c[0] - 0x31
            if index < len(words):
                txt += words[index].decode("utf8")
                input_manager.clear()
                words = []
        if c[0] == 0x20:
            if len(words) > 0:
                txt += words[0].decode("utf8")
                input_manager.clear()
                words = []
        # 删除文字事件
        input_s = input_manager.get_input_code()
        if (c[0] == 0x08 or c[0] == 0x7F) and len(input_s) == 0:
            txt = txt[:-1]
        # 执行输入
        changed = input_manager.input_byte(c[0])
        if changed:
            words = input_manager.some_word(5)
        # 准备显示信息
        input_s = input_manager.get_input_code()
        words_str = ""
        count = 1
        for word in words:
            words_str += ">{}. {} ".format(count,word.decode("utf8"))
            count += 1
        __show(txt,input_s,words_str)
        c = getch()

if __name__ == "__main__":
    try:
        dict_fp = open("pinyin_dict.bin","rb")
        raise Exception("aaa")
    except:
        from pinyin_dict import data
        from io import BytesIO
        dict_fp = BytesIO(data)
    __test(dict_fp)
    