import asyncio
from tiny_http_server import TinyHttpServer, example_server_callback
async def my_callback(hmap,reader):
    if hmap['url'] == '/exit':
        return None
    # return ('stream',{'Content-Type':'text/plain;charset=utf8'},"test.png")
    return ('forbidden',{"a":"B"},'{"file":"test.txt"}')

async def main():
    server1 = TinyHttpServer(host="0.0.0.0", port=8081, callback=example_server_callback)
    await server1.run_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass