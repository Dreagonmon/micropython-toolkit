import os, sys
PLAY32DEV_PATH = "D:/CODE/Python/play32_dev"
sys.path.append(PLAY32DEV_PATH)
app_dir = "D:/CODE/Micropython/ESP32/play32_framework/apps"
import play32env
play32env.setup(app_dir)

import microftpd

if __name__ == "__main__":
    # >>>> test <<<<
    # play32env.start_app("txt_reader")
    fs = microftpd.FTPServer()
    fs.set_host("192.168.31.30")
    fs.run_forever()
