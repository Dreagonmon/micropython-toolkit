from httpkit_server import http_server
def callback(hmap,tmp_body_path):
    if hmap['url'] == '/exit':
        return None
    return ('stream',{'Content-Type':'text/plain;charset=utf8'},"test.txt")
if __name__ == "__main__":
    http_server(8088,callback=callback)