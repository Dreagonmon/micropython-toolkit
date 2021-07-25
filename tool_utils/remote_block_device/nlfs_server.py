import io
import socket

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
        self.open()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.close()

    def open(self):
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
CMD_WRITE = 0x00
CMD_READ = 0x01
CMD_GET_INFO = 0x02
CMD_GET_SERVER_INFO = 0x03
CMD_PING = 0xFF
class ServerUDP():
    def __init__(self, host="0.0.0.0", port=12588, custom_param_size=0):
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.settimeout(0.5)
        udp.bind((host, port))
        self.udp = udp
        self.param_size = self.MINIMAL_PARAM_SIZE + custom_param_size
        self.custom_param_offset = self.MINIMAL_PARAM_SIZE
        self.custom_param_size = custom_param_size
    
    @property
    def MINIMAL_PARAM_SIZE(_):
        return 32

    def do_udp_request(self, block_device: FileBlockDevice, data:bytes, client):
        # block_count = block_device.config.block_count
        # no block_device require:
        cmd = data[0]
        if cmd == CMD_PING:
            self.udp.sendto(bytearray(1), client)
            return
        elif cmd == CMD_GET_SERVER_INFO: # data size 1
            resp = bytearray(8) # fix size 8
            resp[0:4] = int.to_bytes(self.param_size, 4, 'big') # param size
            resp[4:8] = int.to_bytes(self.custom_param_offset, 4, 'big') # custom param offset
            self.udp.sendto(resp, client)
            return
        # block_device required:
        block_size = block_device.config.block_size
        param_size = self.param_size
        packet_size = block_size + param_size
        packet_data = data[param_size:packet_size]
        if cmd == CMD_GET_INFO: # data size param_size
            bs, bc = block_device.get_info()
            resp = bytearray(param_size) # fix size param_size
            resp[0:4] = int.to_bytes(bs, 4, 'big') # block size
            resp[4:8] = int.to_bytes(bc, 4, 'big') # block count
            self.udp.sendto(resp, client)
        elif cmd == CMD_READ: # data size packet_size
            block_num = int.from_bytes(data[2:6], 'big')
            resp_data = block_device.read_block(block_num)
            resp = bytearray(packet_size)
            resp[0] = CODE_SUCCESS
            resp[1] = data[1]
            resp[param_size:packet_size] = resp_data
            self.udp.sendto(resp, client)
        elif cmd == CMD_WRITE: # data size packet_size
            block_num = int.from_bytes(data[2:6], 'big')
            block_device.write_block(block_num, packet_data[:block_size])
            resp = bytearray(packet_size)
            resp[0] = CODE_SUCCESS
            resp[1] = data[1]
            self.udp.sendto(resp, client)
            # print("========")
    
    def run(self, custom_callback):
        try:
            while True:
                try:
                    data, client = self.udp.recvfrom(65536)
                    if data[0] == CMD_GET_SERVER_INFO:
                        self.do_udp_request(None, data, client)
                    else:
                        block_data_size = len(data) - self.custom_param_size - self.MINIMAL_PARAM_SIZE
                        data, file_block_device = custom_callback(self, data, self.MINIMAL_PARAM_SIZE, self.custom_param_size, block_data_size)
                        with file_block_device:
                            self.do_udp_request(file_block_device, data, client)
                except socket.timeout:
                    continue
                except KeyboardInterrupt as e:
                    raise e
                except:
                    import traceback
                    traceback.print_exc()
        except KeyboardInterrupt:
            pass

def __main():
    from littlefs import LittleFS
    from littlefs.context import UserContext
    import mmap
    port = 12588
    block_size = 1024
    block_count = 4096 # 1MB
    file_block_device = FileBlockDevice("lfs.img", block_size, block_count)
    def cus_callback(server, data, m_param_size, c_param_size, block_data_size):
        if block_data_size < 0:
            return data, None
        param = data[0:m_param_size]
        custom_param = data[m_param_size:m_param_size+c_param_size]
        block_data = data[m_param_size+c_param_size:m_param_size+c_param_size+block_data_size]
        return param + custom_param + block_data, file_block_device
    # listen
    server = ServerUDP(port=12588, custom_param_size=16)
    file_block_device.open()
    server.run(cus_callback)
    file_block_device.close()
    # output content
    class FileContext(UserContext):
        def __init__(self, file, buffsize):
            self.buffer = mmap.mmap(file.fileno(), buffsize)
    cfg = file_block_device.config
    context_file = open("lfs.img", "r+")
    context = FileContext(context_file, cfg.buffsize)
    fs = LittleFS(context, block_size=cfg.block_size, block_count=cfg.block_count)
    print(fs.stat("/"))
    print(fs.listdir("/"))
    file_size = fs.stat("README.md").size
    f = fs.open("README.md", "r")
    print(f.read(file_size).decode("utf8"))
    f.close()
    context_file.close()

if __name__ == "__main__":
    __main()