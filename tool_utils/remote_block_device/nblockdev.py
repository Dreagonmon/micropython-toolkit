'''
dev = NetworkBlockDevice("192.168.31.31", 12588)
os.VfsLfs2.mkfs(dev)
os.mount(dev, '/c')
'''
from micropython import const
import socket, select
TIMEOUT = const(5000) # ms
RETRY = const(3)
CODE_SUCCESS = const(0XFF)
CMD_WRITE = const(0x00)
CMD_READ = const(0x01)
CMD_GET_INFO = const(0x02)
CMD_PING = const(0xFF)

pid = 0

class RemoteResourceError(Exception):
    pass

class NetworkBlockDevice:
    def __init__(self, host, port=12588):
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        poller = select.poll()
        poller.register(udp, select.POLLIN)
        address = socket.getaddrinfo(host, port)[0][-1]
        udp.sendto(bytearray([CMD_GET_INFO]), address)
        res = poller.poll(TIMEOUT)
        if len(res) > 0:
            data = udp.recv(512)
        else:
            raise RemoteResourceError()
        block_size = int.from_bytes(data[0:4], 'big')
        block_count = int.from_bytes(data[4:8], 'big')
        assert block_size == 256
        self.udp = udp
        self.poller = poller
        self.address = address
        self.block_size = block_size # block_size
        self.block_count = block_count # block_count
        # print("bdev:", block_size, block_count)

    def __readblock(self, block_num, debug=False):
        global pid
        if debug:
            print("recv_from:", block_num)
        retry = RETRY
        while retry > 0:
            try:
                id = pid % 0xFF
                pid += 1
                req = bytearray(512)
                req[0] = CMD_READ
                req[1] = id
                req[2:6] = int.to_bytes(block_num, 4, 'big')
                self.udp.sendto(req, self.address)
                res = self.poller.poll(TIMEOUT)
                if len(res) > 0:
                    data = self.udp.recv(512)
                    if data[0] == CODE_SUCCESS and data[1] == id:
                        if debug:
                            print(data[256:512])
                        return data[256:512]
            except: pass
            retry -= 1
        raise RemoteResourceError()

    def __writeblock(self, block_num, data, debug=False):
        global pid
        if debug:
            print("send_to:", block_num)
            print(data)
        retry = RETRY
        while retry > 0:
            try:
                id = id = pid % 0xFF
                pid += 1
                req = bytearray(512)
                req[0] = CMD_WRITE
                req[1] = id
                req[2:6] = int.to_bytes(block_num, 4, 'big')
                req[256:512] = data[:256]
                self.udp.sendto(req, self.address)
                res = self.poller.poll(TIMEOUT)
                if len(res) > 0:
                    data = self.udp.recv(512)
                    if data[0] == CODE_SUCCESS and data[1] == id:
                        return
            except: pass
            retry -= 1
        raise RemoteResourceError()

    def readblocks(self, block_num, buf, offset=0):
        # print(">read:",len(buf),"block:",block_num,"offset:",offset)
        blkn = block_num
        size = len(buf)
        index = 0
        if (offset > 0):
            b_end = offset + size
            b_end = 256 if b_end > 256 else b_end
            h_size = b_end - offset
            b_data = self.__readblock(blkn)
            buf[0:h_size] = b_data[offset:b_end]
            index += h_size
            blkn += 1
        while size - index >= 256:
            b_data = self.__readblock(blkn)
            buf[index: index+256] = b_data[:256]
            index += 256
            blkn += 1
        if size != index:
            b_data = self.__readblock(blkn)
            buf[index:size] = b_data[0:size - index]
        # print(buf[:])
        # print("========")

    def writeblocks(self, block_num, buf, offset=0):
        # print(">write:",len(buf),"block:",block_num,"offset:","None" if offset == None else offset)
        # print(buf[:])
        blkn = block_num
        size = len(buf)
        index = 0
        if (offset > 0):
            b_end = offset + size
            b_end = 256 if b_end > 256 else b_end
            h_size = b_end - offset
            b_data = bytearray(self.__readblock(blkn))
            b_data[offset:b_end] = buf[0:h_size]
            self.__writeblock(blkn, b_data)
            index += h_size
            blkn += 1
        while size - index >= 256:
            b_data = buf[index: index+256]
            self.__writeblock(blkn, b_data)
            index += 256
            blkn += 1
        if size != index:
            b_data = bytearray(self.__readblock(blkn))
            b_data[0:size - index] = buf[index:size]
            self.__writeblock(blkn, b_data)
        # print("========")

    def ioctl(self, op, arg):
        if op == 4: # block count
            return self.block_count
        if op == 5: # block size
            return self.block_size
        if op == 6: # block erase, arg is block_num
            try:
                # print(">erase:",arg)
                self.__writeblock(arg, bytearray(256))
                # print("========")
                return 0
            except RemoteResourceError:
                return 16 # Device or resource busy
