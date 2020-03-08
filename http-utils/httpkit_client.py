import sys,gc,os
try:
    import socket
except:
    import usocket as socket
def http_request(url,method="GET",postdata=None,buffersize=64,callback=None,file=None):
    urlinfo = url.split('/', 3)
    host = ''
    path = ''
    for i in range(4):
        if i >= len(urlinfo):
            break
        if i == 2:
            host = urlinfo[2]
        if i == 3:
            path = urlinfo[3]
    hostinfo = host.split(':')
    if len(hostinfo) > 1:
        port = int(hostinfo[-1])
        host = hostinfo[0]
    else:
        port = 80
    addr = socket.getaddrinfo(host, port)[0][-1]
    # post data
    datastr = ""
    if postdata!=None and len(postdata)>0:
        for k in postdata.keys():
            datastr = datastr + k +'='+ postdata[k] +'&'
    # connect
    s = socket.socket()
    s.connect(addr)
    s.send(bytes('%s /%s HTTP/1.0\r\nHost: %s\r\n' % (method.upper(),path, host), 'utf8'))
    s.send(bytes('Content-Length: %s\r\n' % (str(len(bytes(datastr,'utf8')))), 'utf8'))
    s.send(bytes('\r\n','utf8'))
    s.send(bytes(datastr,"utf8"))
    # clean up
    del datastr
    del urlinfo
    del host
    del path
    del hostinfo
    del port
    gc.collect()
    # recive data
    is_head = True
    end_with = b""
    while True:
        data = s.recv(buffersize)
        if data:
            # ignore any header
            if is_head:
                # parse http header
                if b"\r\n\r\n" in data:
                    is_head = False
                    data = data[data.index(b"\r\n\r\n")+4:]
                # case that break on the end
                if len(data)>=3:
                    end_with = end_with + data[0:3]
                else:
                    end_with = end_with + data
                if b"\r\n\r\n" in end_with:
                    is_head = False
                    data = data[4-3+end_with.index(b"\r\n\r\n"):]
                else:
                    end_with = data[-3:]
            if is_head :
                continue
            # process data
            if callback:
                callback(data)
            elif file:
                file.write(data)
            else:
#                print(str(data, 'utf8'), end='')
                sys.stdout.write(data)
        else:
            break
    s.close()

def star_war():
    addr_info = socket.getaddrinfo("towel.blinkenlights.nl", 23)
    addr = addr_info[0][-1]
    s = socket.socket()
    s.connect(addr)
    while True:
        data = s.recv(1024)
        print(str(data, 'utf8'), end='')
