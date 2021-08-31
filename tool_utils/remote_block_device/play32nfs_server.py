import nfs_server
import pyaes, hmac, hashlib, socket, time

PREFIX_NFS = b"nfs_"
SIZE_BUFFER = 4096

def generate_aes_key_and_iv(access_key):
    sha = hmac.HMAC(access_key, access_key, hashlib.sha256).digest()
    return sha[:16], sha[16:]

def generate_timestamp():
    timestamp = int(time.time())
    timestamp = int.to_bytes(timestamp, 8, 'big')
    return timestamp

def generate_sign(access_id, access_key, timestamp, data):
    return hmac.HMAC(access_key, access_id+timestamp+data, hashlib.sha256).digest()

def decode_data(aes_key, iv, data):
    # mode Cipher Block Chaining (CBC)
    data = bytearray(data)
    encoded_len = 0
    enc = pyaes.AESModeOfOperationCBC(aes_key, iv = iv)
    for i in range(len(data) // 16):
        data[i*16:i*16+16] = enc.decrypt(bytes(data[i*16:i*16+16]))
        encoded_len += 16
    return bytes(data)

def encode_data(aes_key, iv, data):
    # mode Cipher Block Chaining (CBC)
    data = bytearray(data)
    encoded_len = 0
    enc = pyaes.AESModeOfOperationCBC(aes_key, iv = iv)
    for i in range(len(data) // 16):
        data[i*16:i*16+16] = enc.encrypt(bytes(data[i*16:i*16+16]))
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

def main():
    block_size = 1024
    block_count = 4096 # 4MB
    file_block_device = nfs_server.FileBlockDevice("lfs.img", block_size, block_count)
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind(("0.0.0.0", 12588))
    while True:
        data, addr = udp.recvfrom(SIZE_BUFFER)
        data = unpack_packet(data, b'12345678')
        with file_block_device:
            resp = nfs_server.do_protocol_udp_request(file_block_device, data)
        resp = pack_packet(b'12345678', b'12345678', resp)
        udp.sendto(resp, addr)

if __name__ == "__main__":
    main()
