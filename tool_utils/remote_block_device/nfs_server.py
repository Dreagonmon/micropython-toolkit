''' 
server.py:
    import nfs_server
    block_size = 1024
    block_count = 4096 # 4MB
    file_block_device = nfs_server.FileBlockDevice("lfs.img", block_size, block_count)
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind(("0.0.0.0", 12588))
    while True:
        data, addr = udp.recvfrom(4096)
        with file_block_device:
            resp = nfs_server.do_protocol_udp_request(file_block_device, data)
        udp.sendto(resp, addr)
'''
import io

class SimpleCFG():
    def __init__(self, block_size, block_count):
        self.__block_size = block_size
        self.__block_count = block_count
    
    @property
    def block_size(self):
        return self.__block_size
    
    @property
    def block_count(self):
        return self.__block_count
    
    @property
    def buffsize(self):
        return self.__block_size * self.__block_count

class FileBlockDevice():
    def __init__(self, file_path, block_size, block_count):
        self.__cfg = SimpleCFG(block_size, block_count)
        self.__path = file_path
        self.__file = None
    
    @property
    def config(self):
        return self.__cfg

    def __enter__(self):
        return self.open()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.close()

    def open(self):
        if self.__file != None:
            return self
        try:
            self.__file = open(self.__path, "rb+")
        except:
            self.__file = open(self.__path, "wb+")
            self.__file.write(bytearray(self.__cfg.buffsize))
            self.__file.flush()
        return self

    def close(self):
        if self.__file == None:
            return
        self.__file.close()
        self.__file = None
    
    def get_info(self):
        return self.__cfg.block_size, self.__cfg.block_count
    
    def read_block(self, block_number):
        offset = block_number * self.__cfg.block_size
        # print(">read:", block_num, "offset:", offset)
        self.__file.seek(offset, io.SEEK_SET)
        return self.__file.read(self.__cfg.block_size)
    
    def write_block(self, block_number, data):
        offset = block_number * self.__cfg.block_size
        self.__file.seek(offset, io.SEEK_SET)
        self.__file.write(data[:self.__cfg.block_size])
        self.__file.flush()

CODE_SUCCESS = 0XFF
SIZE_PARAM = 16
CMD_WRITE = 0x00
CMD_READ = 0x01
CMD_GET_INFO = 0x02
CMD_PING = 0xFF

def do_protocol_udp_request(block_device: FileBlockDevice, data:bytes):
    # no block_device require:
    cmd = data[0]
    if cmd == CMD_PING:
        return bytearray(1)
    # block_device required:
    block_size = block_device.config.block_size
    packet_size = block_size + SIZE_PARAM
    packet_data = data[SIZE_PARAM:packet_size]
    if cmd == CMD_GET_INFO: # data size param_size
        bs, bc = block_device.get_info()
        resp = bytearray(SIZE_PARAM) # fix size param_size
        resp[0:4] = int.to_bytes(bs, 4, 'big') # block size
        resp[4:8] = int.to_bytes(bc, 4, 'big') # block count
        return resp
    elif cmd == CMD_READ: # data size packet_size
        block_num = int.from_bytes(data[2:6], 'big')
        resp_data = block_device.read_block(block_num)
        resp = bytearray(packet_size)
        resp[0] = CODE_SUCCESS
        resp[1] = data[1]
        resp[SIZE_PARAM:packet_size] = resp_data
        return resp
    elif cmd == CMD_WRITE: # data size packet_size
        block_num = int.from_bytes(data[2:6], 'big')
        block_device.write_block(block_num, packet_data[:block_size])
        resp = bytearray(packet_size)
        resp[0] = CODE_SUCCESS
        resp[1] = data[1]
        return resp
        # print("========")
