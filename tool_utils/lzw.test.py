from lzw import Encoder, Decoder
if __name__ == "__main__":
    import gc, sys
    # micropython -X heapsize=2048K lzw.test.py write
    if len(sys.argv) > 1 and sys.argv[1] == "write":
        input_f = open("note.txt", "rb")
        output_f = open("lzw.py.lzw", "wb")
        buffer_size = 1024
        data = input_f.read(buffer_size)
        encoder = Encoder(output_f)
        while len(data) > 0:
            encoder.write(data)
            data = input_f.read(buffer_size)
        encoder.close()
        before = input_f.tell()
        after = output_f.tell()
        input_f.close()
        output_f.close()
        print(f"{before} -> {after}, rate {after/before*100:.2f}%")
    # micropython -X heapsize=32K lzw.test.py
    input_f = open("lzw.py.lzw", "rb")
    output_f = open("lzw.py.bk", "wb")
    tmp_file = open("tmp", "wb+")
    buffer_size = 1024
    decoder = Decoder(input_f, temp_file=tmp_file)
    data = decoder.read(buffer_size)
    # print(gc.mem_alloc())
    while len(data) > 0:
        output_f.write(data)
        data = decoder.read(buffer_size)
        # print(gc.mem_alloc())
    decoder.close()
    input_f.close()
    output_f.close()
    pass