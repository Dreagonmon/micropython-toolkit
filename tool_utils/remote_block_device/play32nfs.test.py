if __name__ == "__main__":
    # setup env
    import sys
    PLAY32DEV_PATH = "D:/CODE/Python/play32_dev"
    sys.path.append(PLAY32DEV_PATH)
    app_dir = "D:/CODE/Micropython/ESP32/play32_framework/apps"
    import play32env
    play32env.setup(app_dir)
    print("==== env inited ====")

if __name__ == "__main__":
    # start test
    from littlefs import LittleFS
    from nbdev import NetworkBlockDevice, ProtocolCache
    from play32nfs import ProtocolPlay32UDP
    class NetworkBlockDeviceContext():
        def __init__(self, nbdev:NetworkBlockDevice):
            self.__nbdev = nbdev
        
        def read(self, cfg, block: int, off: int, size: int) -> bytearray:
            assert cfg.block_size == self.__nbdev.ioctl(5, None)
            data = bytearray(size)
            self.__nbdev.readblocks(block, data, off)
            return data
        
        def  prog(self, cfg, block: int, off: int, data: bytes) -> int:
            assert cfg.block_size == self.__nbdev.ioctl(5, None)
            self.__nbdev.writeblocks(block, data, off)
            return 0
        
        def erase(self, cfg, block: int) -> int:
            assert cfg.block_size == self.__nbdev.ioctl(5, None)
            self.__nbdev.ioctl(6, block)
            return 0
        
        def sync(self, cfg) -> int:
            return 0
    pudp = ProtocolPlay32UDP("192.168.31.37", 12588)
    pudp = ProtocolCache(pudp)
    dev = NetworkBlockDevice(pudp)
    context =  NetworkBlockDeviceContext(dev)
    lfs = LittleFS(context, block_size=dev.ioctl(5, None), block_count=dev.ioctl(4, None))
    count = 0
    while True:
        f = lfs.open("README.md", 'w')
        f.write("# Hello Dragon!\n".encode("utf8"))
        f.close()
        f = lfs.open("README.md", 'r')
        print(count, f.read(1024))
        f.close()
        count += 1