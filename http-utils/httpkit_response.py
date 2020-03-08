# text/plain, text/html, text/css
# image/gif, image/png, image/jpeg, image/bmp
# application/javascript, application/octet-stream
import os
coding = 'utf8'
memi = {
'txt':'text/plain',
'html':'text/html',
'xhtml':'text/html',
'css':'text/css',
'svg':'image/svg',
'gif':'image/gif',
'png':'image/png',
'bmp':'image/bmp',
'jpg':'image/jpeg',
'jpeg':'image/jpeg',
'ico':'image/ico',
'js':'application/javascript',
'':'application/octet-stream',
}
header_end = '\r\n'
header_200 = 'HTTP/1.0 200 OK\r\n'
header_404 = 'HTTP/1.0 404 Not Found\r\n'
header_500 = 'HTTP/1.0 500 Internal Server Error\r\n'
header_text = 'Content-Type: text/plain; charset=%s\r\n' % (coding,)
header_html = 'Content-Type: text/html; charset=%s\r\n' % (coding,)

def header_301(location):
    return 'HTTP/1.0 301 Moved Permanently\r\n'+'Location: '+location+'\r\n'
def header_302(location):
    return 'HTTP/1.0 302 Moved Temporarily\r\n'+'Location: '+location+'\r\n'
def header_static(path):
    ext = (path[path.rfind('.')+1:]).lower()
    if ext in memi.keys():
        ext = memi[ext]
    else :
        ext = memi['']
    return 'Content-Type: %s; charset=UTF-8\r\n' % (ext,)
def header_from_dict(header):
    if header==None or len(header)<=0:
        return ""
    head = ""
    for k in header.keys():
        head = head + k +': '+ header[k] +'\r\n'
    return head
def header_text_content_length(content):
    return 'Content-Length: %s\r\n' % (str(len(bytes(content,coding))),)
def header_stream_content_length(stream_size):
    return 'Content-Length: %s\r\n' % (str(stream_size),)

def send(cl,text):
    cl.send(bytes(text,coding))
def response(resp,cl,buffersize=64):
    # resp: (type,header,content)
    #---------------------
    # type    | content
    #---------------------
    # text    : content as text √
    # html    : content as html √
    # redirect: content as redirect location √
    # stream  : content is stream file path √
    # static  : content is static file path √
    # raw     : raw stream file path √
    type,header,content = resp
    if type == 'text':
        send(cl,header_200)
        send(cl,header_text)
        send(cl,header_from_dict(header))
        send(cl,header_text_content_length(content))
        send(cl,header_end)
        send(cl,content)
    if type == 'html':
        send(cl,header_200)
        send(cl,header_html)
        send(cl,header_from_dict(header))
        send(cl,header_text_content_length(content))
        send(cl,header_end)
        send(cl,content)
    if type == 'redirect':
        send(cl,header_302(content))
        send(cl,header_stream_content_length(0))
        send(cl,header_end)
    if type == 'stream':
        # header
        try:
            file = open(content,'rb')
            s_size = os.stat(content)[6]
        except:
            send(cl,header_500)
            send(cl,header_html)
            send(cl,header_end)
            send(cl,'<h1>500 Stream File Not Found</h1>')
            return
        send(cl,header_200)
        send(cl,header_from_dict(header))
        send(cl,header_stream_content_length(s_size))
        send(cl,header_end)
        # content
        while True:
            data = file.read(buffersize)
            if not data or len(data)==0:
                break
            cl.sendall(data)
        file.close()
    if type == 'static':
        # header
        try:
            file = open(content,'rb')
            s_size = os.stat(content)[6]
        except:
            send(cl,header_404)
            send(cl,header_html)
            send(cl,header_end)
            send(cl,'<h1>404 Not Found</h1>')
            return
        send(cl,header_200)
        send(cl,header_static(content))
        send(cl,header_from_dict(header))
        send(cl,header_stream_content_length(s_size))
        send(cl,header_end)
        # content
        while True:
            data = file.read(buffersize)
            if not data or len(data)==0:
                break
            cl.sendall(data)
        file.close()
    if type == 'raw':
        # header
        try:
            file = open(content,'rb')
        except:
            send(cl,header_500)
            send(cl,header_html)
            send(cl,header_end)
            send(cl,'<h1>500 Stream File Not Found</h1>')
            return
        # content
        while True:
            data = file.read(buffersize)
            if not data or len(data)==0:
                break
            cl.sendall(data)
        file.close()