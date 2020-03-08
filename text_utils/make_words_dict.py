from functools import total_ordering
from typing import Mapping, List

@total_ordering
class Word():
    '''词条类，由拼音、词汇和权重组成'''
    def __init__(self,word:str,pinyin:str,freq:int):
        self.word:str = word
        self.pinyin:str = pinyin.lower()
        self.freq:int = freq
    def __lt__(self,other):
        return self.freq < other.freq
    def __repr__(self):
        return "{:s} {:s} {:d}".format(self.word,self.pinyin,self.freq)


def get_all_words(dict_path:str,source_encoding:str="utf8",target_encoding:str="utf8",word_length:int=4,min_freq:int = 1):
    '''读取文本并转换成Word对象列表，可以指定编码、词汇长度和词频'''
    f = open(dict_path,"r",encoding=source_encoding)
    lines = f.read().split("\n")
    words:List[Word] = []
    for line in lines:
        if line == "":
            continue
        tmp = line.split()
        word = tmp[0]
        freq = int(tmp[-1])
        pinyin = "".join(tmp[1:-1])
        # 只保留配置词频以上的词汇
        if freq < min_freq:
            continue
        # 只保留指定编码里面的词汇
        try:
            word.encode(target_encoding,errors='strict')
        except:
            continue
        # 单片机性能有限，只保留指定长度的词汇
        if len(word) > word_length:
            continue
        words.append(Word(word,pinyin,freq))
    return words
def arrange_pinyin(words:List[Word]):
    '''将Word对象列表转换成根据拼音的MAP'''
    pinyin:Mapping[str,List[Word]] = {}
    for word in words:
        if not word.pinyin in pinyin:
            pinyin[word.pinyin] = []
        pinyin[word.pinyin].append(word)
    # 按照词频排序
    for key in pinyin:
        pinyin[key].sort(reverse=True)
    return pinyin
def pinyin_9key(pinyin:str):
    '''将拼音序列转换成九键的数字序列'''
    num = ""
    for ch in pinyin:
        ch = ch.lower()
        if ch in ["a","b","c"]:
            num += "2"
        if ch in ["d","e","f"]:
            num += "3"
        if ch in ["g","h","i"]:
            num += "4"
        if ch in ["j","k","l"]:
            num += "5"
        if ch in ["m","n","o"]:
            num += "6"
        if ch in ["p","q","r","s"]:
            num += "7"
        if ch in ["t","u","v"]:
            num += "8"
        if ch in ["w","x","y","z"]:
            num += "9"
    return num
def arrange_9key(words:List[Word]):
    '''将Word对象列表转换成根据九键拼音的MAP'''
    nkey:Mapping[str,List[Word]] = {}
    for word in words:
        num = pinyin_9key(word.pinyin)
        if not num in nkey:
            nkey[num] = []
        nkey[num].append(word)
    # 按照词频排序
    for key in nkey:
        nkey[key].sort(reverse=True)
    return nkey
def make_words_dict(cmap:Mapping[str,List[Word]],target_encoding:str="utf8",info:bool=False):
    '''根据按键码MAP和目标编码生成输入法字典文件
    |1字节下一索引数量|若干5字节(|1字节a~z|4绝对地址|)下一状态块地址|[utf8编码的所有单个汉字|1字节0x00]...|1字节0x00|
    即最后两个0x00表示一个数据块的结束'''
    # 深度优先，递归生成二进制文件
    return make_data_block(cmap,"",0,target_encoding,info=info)
def make_data_block(cmap:Mapping[str,List[Word]],pre:str,offset:int,target_encoding:str="utf8",info:bool=False):
    ''' pre:当前编码
        cmap: 按键码map，为提高性能，需要保证map里都是符合pre前缀的编码
        offset: 当前偏移量
        target_encoding: 目标字典编码'''
    # 获取当前编码的词汇
    data:bytearray = bytearray()
    words:List[Word] = []
    if pre in cmap:
        words.extend(cmap[pre])
    # 获取下一个字符，占位待更新
    next_char:Mapping[str:Mapping[str,List[Word]]] = {}
    char_pos = len(pre)
    for code in cmap:
        if len(code) <= char_pos:
            continue
        c = code[char_pos]
        if not c in next_char:
            next_char[c] = {}
        next_char[c][code] = cmap[code]
    # 生成下一字符绝对地址编码，一次循环产生5字节
    data.extend(len(next_char.keys()).to_bytes(1,"big",signed=False))
    for c in next_char:
        data.extend(c.encode("ascii")) #标记是哪一个字符
        data.extend(bytearray(4)) #32位绝对地址占位符
    # 生成当前编码的候选词
    for word in words:
        data.extend(word.word.encode(target_encoding))
        data.append(0x00)
    data.append(0x00)
    # 开始递归
    count = 0
    path_count = 0 # 可选拼音路径数
    for c in next_char:
        new_pre = pre + c
        block, sub_path_count, sub_words = make_data_block(next_char[c],new_pre,offset+len(data),target_encoding)
        # 当所有可能的路径数为1，且本块没有候选词的时候，将下一块合并到当前块
        if sub_path_count==1 and len(next_char.keys())==1 and len(words)==0:
            # 重新生成本块内容
            words = sub_words
            data = bytearray()
            data.extend((0).to_bytes(1,"big",signed=False)) # 没有下一块了
            for word in words:
                data.extend(word.word.encode(target_encoding))
                data.append(0x00)
            data.append(0x00)
            break
        path_count += sub_path_count
        # 有数据返回，更新数据块地址和数据块
        data[count*5+2:count*5+6] = (offset+len(data)).to_bytes(4,"big",signed=False)
        data.extend(block) #直接在数据块后面拓展，即匹配了绝对地址
        count += 1
        if info:
            print("\rstart with: {:<4} ({:>3}/{:<3})".format(c,count,len(next_char.keys())))
    if path_count == 0:
        path_count = 1
    # 返回数据块，路径数，本块的候选词
    return data, path_count, words

def __main():
    # 获取词汇列表
    words = get_all_words("list.txt","utf8","gb2312",1,100)
    # 整理词汇列表
    pinyin = arrange_pinyin(words)
    # pinyin = arrange_9key(words)
    # 开始生成字典
    data,_,_ = make_words_dict(pinyin,"gb2312",info=True)
    with open("dict.bin","wb") as f:
        f.write(data)
    # 输出信息
    print("字典大小:",len(data)/1024,"Kbytes")
    print("词汇数量:",len(words))
    print("拼音数量:",len(pinyin.keys()))
    wmax = 0
    wmaxk = ""
    for k in pinyin:
        if len(pinyin[k]) > wmax:
            wmax = len(pinyin[k])
            wmaxk = k
    print("最大同码:",wmax)
    print("最大同码:",wmaxk)

if __name__ == "__main__":
    __main()