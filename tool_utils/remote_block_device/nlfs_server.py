import io
import mmap
from littlefs import LittleFS
from littlefs.context import UserContext
import socket
BLOCK_SIZE = 256
CODE_SUCCESS = 0XFF
CMD_WRITE = 0x00
CMD_READ = 0x01
CMD_GET_INFO = 0x02
CMD_PING = 0xFF

class SimpleCFG():
    block_size = 0
    block_count = 0

class BlockDeviceFile(UserContext):
    def __init__(self, file, buffsize: int) -> None:
        self.buffer = mmap.mmap(file.fileno(), buffsize)

if __name__ == "__main__":
    # block_count = 524288 # 128MB
    block_count = 4096 # 1MB
    port = 12588
    try:
        fs_file = open("lfs.img", "rb+")
        print("fsf loaded.")
    except:
        fs_file = open("lfs.img", "wb+")
        fs_file.write(bytearray(BLOCK_SIZE*block_count))
        fs_file.flush()
        print("fsf inited.")
    # listen
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.settimeout(0.5)
    udp.bind(('0.0.0.0', port))
    try:
        while True:
            try:
                data, client = udp.recvfrom(512)
            except socket.timeout:
                continue
            cmd = data[0]
            packet_data = data[512-BLOCK_SIZE:512]
            if cmd == CMD_PING:
                udp.sendto(bytearray(1), client)
            elif cmd == CMD_GET_INFO:
                resp = b''
                resp += int.to_bytes(BLOCK_SIZE, 4, 'big') # block size
                resp += int.to_bytes(block_count, 4, 'big') # block count
                udp.sendto(resp, client)
            elif cmd == CMD_READ:
                block_num = int.from_bytes(data[2:6], 'big')
                offset = block_num * BLOCK_SIZE
                # print(">read:", block_num, "offset:", offset)
                fs_file.seek(offset, io.SEEK_SET)
                resp_data = fs_file.read(BLOCK_SIZE)
                resp = bytearray(512)
                resp[0] = CODE_SUCCESS
                resp[1] = data[1]
                resp[512-BLOCK_SIZE:512] = resp_data
                udp.sendto(resp, client)
            elif cmd == CMD_WRITE:
                block_num = int.from_bytes(data[2:6], 'big')
                offset = block_num * BLOCK_SIZE
                # print(">write:", block_num, "offset:", offset)
                # print(packet_data[:BLOCK_SIZE])
                fs_file.seek(offset, io.SEEK_SET)
                fs_file.write(packet_data[:BLOCK_SIZE])
                resp = bytearray(512)
                resp[0] = CODE_SUCCESS
                resp[1] = data[1]
                udp.sendto(resp, client)
                # print("========")
    except KeyboardInterrupt:
        pass
    # output content
    fs_file.flush()
    context = BlockDeviceFile(fs_file, BLOCK_SIZE*block_count)
    fs = LittleFS(context, block_size=BLOCK_SIZE, block_count=block_count)
    print(fs.stat("/"))
    print(fs.listdir("/"))
    print(context.buffer[:256])
    context.buffer.close()
    fs_file.close()
