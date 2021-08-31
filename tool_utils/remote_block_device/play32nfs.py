from uhashlib import sha256
from ucryptolib import aes
from utils.hmac import HMAC
from utils.time_helper import EPOCH_TIME_DIFFER
from micropython import const
from nbdev import RemoteResourceError
import utime, usocket

CODE_SUCCESS = const(0XFF)
SIZE_PARAM = const(16)
SIZE_BUFFER = const(4096)
CMD_WRITE = const(0x00)
CMD_READ = const(0x01)
CMD_GET_INFO = const(0x02)
CMD_GET_SERVER_INFO = const(0x03)
CMD_PING = const(0xFF)
PREFIX_NFS = b"nfs_"

def generate_aes_key_and_iv(access_key):
    sha = HMAC(access_key, access_key, sha256).digest()
    return sha[:16], sha[16:]

def generate_timestamp():
    timestamp = int(utime.time()) + EPOCH_TIME_DIFFER
    timestamp = int.to_bytes(timestamp, 8, 'big')
    return timestamp

def generate_sign(access_id, access_key, timestamp, data):
    # generate 32 bytes sign
    return HMAC(access_key, access_id+timestamp+data, sha256).digest()

def encode_data(aes_key, iv, data):
    # mode Cipher Block Chaining (CBC)
    data = bytearray(data)
    encoded_len = 0
    enc = aes(aes_key, 2, iv)
    for i in range(len(data) // 16):
        data[i*16:i*16+16] = enc.encrypt(data[i*16:i*16+16])
        encoded_len += 16
    return bytes(data)

def decode_data(aes_key, iv, data):
    # mode Cipher Block Chaining (CBC)
    data = bytearray(data)
    encoded_len = 0
    enc = aes(aes_key, 2, iv)
    for i in range(len(data) // 16):
        data[i*16:i*16+16] = enc.decrypt(data[i*16:i*16+16])
        encoded_len += 16
    return bytes(data)

def pack_packet(access_id, access_key, data):
    # access_id, access_key: 8 bytes
    aes_key, iv = generate_aes_key_and_iv(access_key)
    data = encode_data(aes_key, iv, data)
    tms = generate_timestamp() # 8 bytes
    sign =generate_sign(access_id, access_key, tms, data) # 32 bytes
    return PREFIX_NFS + access_id + tms + sign + data # 4 + 48 bytes + len(data)

def unpack_packet(packet, access_key):
    assert packet[0:4] == PREFIX_NFS
    access_id = packet[4:12]
    aes_key, iv = generate_aes_key_and_iv(access_key)
    tms = packet[12:20]
    remote_sign = packet[20:52]
    data = packet[52:]
    sign = generate_sign(access_id, access_key, tms, data)
    assert sign == remote_sign
    return decode_data(aes_key, iv, data)

class ProtocolPlay32UDP:
    def __init__(self, host, port=12588, retry=3, timeout_ms=500, access_id=b'12345678', access_key=b'12345678'):
        udp = usocket.socket(usocket.AF_INET, usocket.SOCK_DGRAM)
        udp.settimeout(timeout_ms/1000)
        address = usocket.getaddrinfo(host, port)[0][-1]
        # get remote block device info
        req = bytearray(SIZE_PARAM)
        req[0] = CMD_GET_INFO
        req = pack_packet(access_id, access_key, req)
        udp.sendto(req, address)
        data = udp.recv(SIZE_BUFFER)
        data = unpack_packet(data, access_key)
        self.block_size = int.from_bytes(data[0:4], 'big')
        self.block_count = int.from_bytes(data[4:8], 'big')
        self.pid = 0 # request id
        self.udp = udp
        self.address = address
        self.retry = retry
        self.packet_size = SIZE_PARAM + self.block_size
        self.access_id = access_id
        self.access_key = access_key
    
    def get_info(self):
        return self.block_size, self.block_count

    def read_block(self, block_num):
        # print("read:", block_num)
        retry = self.retry
        access_id = self.access_id
        access_key =self.access_key
        while retry > 0:
            try:
                id = self.pid % 0xFF
                self.pid += 1
                req = bytearray(self.packet_size)
                req[0] = CMD_READ
                req[1] = id
                req[2:6] = int.to_bytes(block_num, 4, 'big')
                req = pack_packet(access_id, access_key, req)
                self.udp.sendto(req, self.address)
                data = self.udp.recv(SIZE_BUFFER)
                data = unpack_packet(data, access_key)
                if data[0] == CODE_SUCCESS and data[1] == id:
                    return data[SIZE_PARAM:self.packet_size]
            except: pass
            retry -= 1
        raise RemoteResourceError()
    
    def write_block(self, block_num, data):
        # print("write:", block_num)
        retry = self.retry
        access_id = self.access_id
        access_key =self.access_key
        while retry > 0:
            try:
                id = self.pid % 0xFF
                self.pid += 1
                req = bytearray(self.packet_size)
                req[0] = CMD_WRITE
                req[1] = id
                req[2:6] = int.to_bytes(block_num, 4, 'big')
                req[SIZE_PARAM:self.packet_size] = data[:self.block_size]
                req = pack_packet(access_id, access_key, req)
                self.udp.sendto(req, self.address)
                data = self.udp.recv(SIZE_BUFFER)
                data = unpack_packet(data, access_key)
                if data[0] == CODE_SUCCESS and data[1] == id:
                    return
            except: pass
            retry -= 1
        raise RemoteResourceError()

