import network
from tiny_http_server import get_url_path, get_url_params, TinyHttpServer
try:
    import ujson as json
except ImportError:
    import json

# setup network
ap_if = network.WLAN(network.AP_IF)
ap_if.config(essid="Micro_Controler")
ap_if.active(True)
def ip():
    print(ap_if.ifconfig()[0])

INDEX_FILE = '/resource/controller.html'
__buttons = [] # buttons = [[x, y, w, h, 'label'],] # x,y,w,h in range [0, 100]
__callback = None # async def btn_callback(btn_label): -> None

def init(buttons, callback):
    global __buttons, __callback
    __buttons = buttons
    __callback = callback

async def server_callback(header_map, body_reader):
    # url
    url = header_map['url']
    # path
    path = get_url_path(url)
    # query data
    if path == '/' or path == 'index.html':
        return ('static', {}, INDEX_FILE)
    elif path == '/buttons':
        return ('json', {}, json.dumps(__buttons))
    elif path == '/click':
        pos = url.rfind("?text=")
        text = url[pos+6:]
        if __callback != None:
            await __callback(text)
        return ('text', {}, 'ok')
    return ('static', {}, '/resource'+path)

control_server = TinyHttpServer(host='0.0.0.0', port=80, callback=server_callback, buffer_size=1024)
