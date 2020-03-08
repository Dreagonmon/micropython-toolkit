import sys,gc,os,httpkit_response
try:
    import socket
except:
    import usocket as socket
import uselect
request_body_tmp_file = 'req_body.tmp'
# http server will blocking main thread!
def http_server(port,buffersize=64,callback=None,once=False,timeout=0.5):
    # callback(header_map,tmp_file_path):=>(str,str)
    # return(type,header,content)
    #        string,dict,string
    # text: content as text
    # html: content as html
    # stream: content is stream file path
    # static: content is static file path
    # redirect: content as redirect location
    # raw: raw stream path
    addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(0)
    print('listening on', addr)
    while True:
        try:
            gc.collect()
            cl, addr = s.accept()
            cl.settimeout(timeout)
            hmap = {}
            print('--------')
            print('client connected from', addr)
            # header
            print('read header')
            first_line = None
            while first_line == None or len(first_line)==0:
                first_line = str(cl.readline(),'utf-8')
            httph = first_line.split(' ',2)
            hmap['mathod'] = httph[0]
            hmap['url'] = httph[1]
            del first_line
            del httph
            line = None
            sp = -1
            param = None
            value = None
            while True:
                # read header line by line
                gc.collect()
                line = cl.readline()
                if not line or line == b'\r\n':
                    break
                line = str(line,'utf-8')
                sp = line.find(':')
                if sp > 0:
                    param = line[0:sp].strip().lower()
                    value = line[sp+1:].strip()
                    hmap[param] = value
            del line
            del sp
            del param
            del value
            gc.collect()
            print('url: '+hmap['url'])
            print('read body')
            # content
            reqf = open(request_body_tmp_file,'wb')
            if 'content-length' in hmap.keys():
                readed = 0
                clength = int(hmap['content-length'])
                while readed < clength:
                    nlength = readed + buffersize
                    if nlength > clength:
                        nlength = clength
                    data = cl.read(nlength-readed)
                    readed = nlength
                    reqf.write(data)
                    pass
                del readed
                del clength
                del data
            reqf.close()
            del reqf
            gc.collect()
            print(gc.mem_free())
            print('response')
            # content
            # deal with request
            if callback != None:
                # response
                resp = callback(hmap,request_body_tmp_file)
                # return None to end loop
                if resp == None:
                    cl.send(bytes('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=UTF-8\r\n\r\n','utf8'))
                    cl.send(bytes('<h1>Server Exit!</h1>','utf8'))
                    cl.close()
                    s.close()
                    return
                gc.collect()
                print('send response')
                httpkit_response.response(resp,cl,buffersize)
                del resp
            else:
                cl.send(bytes('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=UTF-8\r\n\r\n','utf8'))
                cl.send(bytes('<h1>Hello World!</h1>','utf8'))
            cl.close()
            #print(hmap)
            print('end requests')
            del cl
            del addr
            del hmap
            gc.collect()
            print(gc.mem_free())
            print('--------')
            if once:
                break
        except OSError as e:
            try:
                cl.close()
            except:
                pass
            gc.collect()
            sys.print_exception(e)
            print('--------')
    s.close()
    gc.collect()
    pass
