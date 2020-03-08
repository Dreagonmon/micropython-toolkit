# This file is executed on every boot (including wake-boot from deepsleep)
import esp
esp.osdebug(None)
import network

wifi_sta = network.WLAN(network.STA_IF)
wifi_ap = network.WLAN(network.AP_IF)
# set wifi config
wifi_sta.active(True)
wifi_sta.connect('Dreagonmon-APpriv','09595715')
# set ap
wifi_ap.active(True)
wifi_ap.config(essid='MicroDragon',password='zhaoan2k',authmode=network.AUTH_WPA_WPA2_PSK)
#wifi_ap.active(True)
# start webrepl
import webrepl
webrepl.stop()
# tmp dir

# clean up
del esp
del network
#del wifi_sta
#del wifi_ap
import gc
gc.collect()
del gc
from gc import mem_free as free