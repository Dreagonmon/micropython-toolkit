import asyncio, threading, os, json
from . import ssd1306img
from aiohttp import web
from io import BytesIO
from base64 import b64encode
from typing import Mapping

# config
__HOST = "0.0.0.0"
__PORT = 8848

# global var
__server_thread = None
__httpd = None
__loop = None
__stop = False
__screens = {}
__lock_table = {} # screen_name -> lock
__resp_list = []

def start():
    global  __server_thread
    # 不要重复启动服务
    if __server_thread != None and __server_thread.is_alive():
        return
    __server_thread = threading.Thread(target=__start_server)
    __server_thread.setDaemon(True)
    __server_thread.start()

def setup_screen(name,width,height,buffer,invert=True,buttons=[],button_callback=None):
    assert buffer != None
    assert width <= 128 and width >= 2
    assert height <= 64 and height >= 2
    __screens[name] = {"buffer":buffer,"width":width,"height":height,"invert":invert,"buttons":buttons,"keypad":{},"callback":button_callback}

def remove_screen(name):
    if name in __screens:
        del __screens[name]

def update_screen(name,buffer):
    if __loop == None:
        return
    if name in __screens:
        __screens[name]["buffer"] = buffer
    asyncio.run_coroutine_threadsafe(__notify(name),__loop)

def is_key_down(name,key):
    if name in __screens and key in __screens[name]["keypad"]:
        return __screens[name]["keypad"][key]
    return False

def stop():
    global __stop
    __stop = True

def is_running():
    return __server_thread != None and __server_thread.is_alive()

async def __stop_server():
    global __stop, __httpd
    __stop = False
    while not __stop:
        await asyncio.sleep(0.5)
    print("停止服务...")
    await __httpd.cleanup()
    loop = asyncio.get_event_loop()
    loop.call_soon(lambda loop: loop.stop(),loop)

async def __run_server():
    global __httpd
    app = web.Application()
    # 添加启动时任务
    app.on_startup.append(__before_server_start)
    # 添加应用关闭时回调
    app.on_shutdown.append(__before_server_stop)
    app.add_routes([
        web.post("/screen_event/{name}",__screen_event),
        web.get("/screen_event/{name}",__screen_event),
        web.post("/keypad_event/{name}/{key}/{op}",__keypad_event),
        web.get("/keypad_event/{name}/{key}/{op}",__keypad_event),
        web.get("/{name}",__screen_page),
        web.get("/",__index_page),
    ])
    __httpd = web.AppRunner(app)
    await __httpd.setup()
    site = web.TCPSite(__httpd, __HOST, __PORT)
    await site.start()
    print("服务启动在 {:s}:{:d}\n浏览器访问以获取ssd1306屏幕内容".format(__HOST,__PORT))
async def __before_server_start(app):
    app['keep_alive'] = asyncio.ensure_future(__keep_alive_task())
async def __before_server_stop(app):
    app['keep_alive'].cancel()
    await app['keep_alive']

def __start_server():
    global __loop
    __loop = asyncio.get_event_loop_policy().new_event_loop()
    asyncio.get_event_loop_policy().set_event_loop(__loop)
    asyncio.run_coroutine_threadsafe(__run_server(),__loop)
    asyncio.run_coroutine_threadsafe(__stop_server(),__loop)
    __loop.run_forever()

# web请求相关方法
# 主页
async def __index_page(request):
    with open(os.path.dirname(__file__)+"/index.html","r",encoding="utf-8") as f:
        html = f.read()
    html = html.replace("{screens:s}",json.dumps(list(__screens.keys())))
    return web.Response(content_type="text/html",body=html)
# 屏幕页
async def __screen_page(request):
    name = request.match_info["name"]
    if name not in __screens:
        return web.Response(content_type="text/html",body="<h1>Screen Not Exist</h1>")
    with open(os.path.dirname(__file__)+"/screen.html","r",encoding="utf-8") as f:
        html = f.read()
    html = html.replace("{name:s}",name).replace("{buttons:s}",json.dumps(__screens[name]["buttons"]))
    return web.Response(content_type="text/html",body=html)
# 屏幕事件
def __get_lock(name):
    if not name in __lock_table:
        __lock_table[name] = asyncio.Condition()
    return __lock_table[name]
async def __notify(name):
    if not name in __lock_table:
        return False
    lock = __lock_table[name]
    await lock.acquire()
    try:
        lock.notify_all()
        return True
    except:
        return False
    finally:
        lock.release()
def __get_image_data_url(name):
    if not name in __screens.keys():
        return ""
    screen = __screens[name]
    img = ssd1306img.emu1306(screen["buffer"],screen["width"],screen["height"],invert=screen["invert"])
    output = BytesIO()
    img.save(output,format="png")
    data = b64encode(output.getvalue()).decode("utf-8")
    output.close()
    data = "data:image/png;base64," + data
    return data
async def __keep_alive_task():
    # 定时发送消息，防止连接关闭
    try:
        while True:
            await asyncio.sleep(30) #30s
            for resp in __resp_list:
                try:
                    await resp.write(":ping\r\n".encode("utf-8"))
                except:
                    __resp_list.remove(resp)
    except asyncio.CancelledError:
        pass
async def __screen_event(request):
    name = request.match_info["name"]
    resp = web.StreamResponse()
    # 设置响应头
    resp.headers['Content-Type'] = 'text/event-stream'
    resp.headers['Cache-Control'] = 'no-cache'
    resp.headers['Connection'] = 'keep-alive'
    resp.headers['X-Accel-Buffering'] = 'no'
    resp.enable_chunked_encoding()
    # 开始ServeSendEvent
    await resp.prepare(request)
    lock = __get_lock(name)
    __resp_list.append(resp)
    try:
        await resp.write(":connected\r\n".encode("utf-8"))
        # 激活一次事件
        await resp.write("event: {:s}\r\ndata: {:s}\r\n\r\n".format("screen_update",__get_image_data_url(name)).encode("utf-8"))
        while True:
            await lock.acquire()
            try:
                # 等待事件唤醒
                await lock.wait()
                await resp.write("event: {:s}\r\ndata: {:s}\r\n\r\n".format("screen_update",__get_image_data_url(name)).encode("utf-8"))
            finally:
                lock.release()
    finally:
        __resp_list.remove(resp)
    # 结束
    await resp.write_eof()
    return resp
# 按钮事件
async def __keypad_event(request):
    name = request.match_info["name"]
    key = request.match_info["key"]
    op = request.match_info["op"]
    assert op == "down" or op == "up"
    if name in __screens:
        if op == "down":
            __screens[name]["keypad"][key] = True
        else:
            __screens[name]["keypad"][key] = False
        # 如果设置过回调则调用
        if __screens[name]["callback"] != None:
            __screens[name]["callback"](key,op)
        return web.Response(body="ok")
    return web.Response(body="failed")