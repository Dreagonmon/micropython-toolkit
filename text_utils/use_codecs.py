'''
编码转换辅助文件，文件开头：|2 b"CO"|4记录的编码数量，即 文件大小=数量*(源长度+目标长度)+8|1源长度|1目标长度|
之后 |源编码|目标编码| 为一组，按照源编码从小到大排列，使用时二分搜索查找对应的编码转换
'''
import coding

def __bin_search_in_file(file_handle,target,start,end,s_size,t_size,buffer_size=0,buffer=None):
    if end <= start:
        # not found
        return False
    block_size = s_size + t_size
    # use buffer speedup search
    if (end - start <= buffer_size//block_size):
        if (buffer == None):
            # first time, create buffer
            file_handle.seek(start*block_size)
            data = file_handle.read((end-start)*block_size)
            buffer = memoryview(data)
            end = end - start
            start = 0
        center = (end + start) // 2
        pos = center * (s_size + t_size)
        value = int.from_bytes(buffer[pos:pos+s_size],"big",signed=False)
        # print('buff',start,center,end,"0x{:X}".format(value))
    else:
        # read from file
        center = (end + start) // 2
        pos = center * (s_size + t_size) + 8 #要跳过文件头8字节
        file_handle.seek(pos)
        value = int.from_bytes(file_handle.read(s_size),"big",signed=False)
        # print('file',start,end,end-start,"0x{:X}".format(value))
    # compare
    if value < target:
        return __bin_search_in_file(file_handle,target,center+1,end,s_size,t_size,buffer_size=buffer_size,buffer=buffer)
    if value > target:
        return __bin_search_in_file(file_handle,target,start,center,s_size,t_size,buffer_size=buffer_size,buffer=buffer)
    # find!
    if (end - start <= buffer_size//block_size):
        # find in buffer
        data = bytes(buffer[pos+s_size:pos+block_size])
        return data
    else:
        # find in file
        return file_handle.read(t_size)

def convert(byts,codec_file,buffer_size=0):
    with open(codec_file,"rb") as f:
        magic = f.read(2)
        assert magic == b"CO"
        count = int.from_bytes(f.read(4),"big",signed=False)
        s_size = int.from_bytes(f.read(1),"big",signed=False)
        t_size = int.from_bytes(f.read(1),"big",signed=False)
        target = int.from_bytes(byts,"big",signed=False)
        resault = __bin_search_in_file(f,target,0,count,s_size,t_size,buffer_size=buffer_size)
        return resault

def main():
    unic = coding.UTF_8.u82unicode("神".encode("utf8"))
    byts = convert(unic.to_bytes(2,"big",signed=False),"unicode2gb2312.codec",buffer_size=128)
    print("0x{:X}".format(unic),byts.decode("gb2312"))
    pass

if __name__ == "__main__":
    main()