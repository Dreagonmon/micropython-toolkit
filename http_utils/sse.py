"""
Server Sent Event
"""
import socket

class EventSource:
    def __init__(self, buffer_size=100):
        self.s = None # type: socket.socket
        self.chunked = False
        self.chunk_remain_size = 0
        self.chunk_reading = False
        self.last_event = ""
        self.buffer = bytearray()

    def connect(self, url, cookies=None):
        try:
            proto, _, host, path = url.split("/", 3)
        except ValueError:
            proto, _, host = url.split("/", 2)
            path = ""
        if proto == "http:":
            port = 80
        elif proto == "https:":
            import ussl
            port = 443
        else:
            raise ValueError("Unsupported protocol: " + proto)

        if ":" in host:
            host, port = host.split(":", 1)
            port = int(port)

        ai = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)
        ai = ai[0]

        s = socket.socket(ai[0], ai[1], ai[2])
        s.settimeout(5.0)
        try:
            # print('Socket connect')
            s.connect(ai[-1])
            if proto == "https:":
                s = ussl.wrap_socket(s, server_hostname=host)
            # print('http start')
            s.write(b"GET /%s HTTP/1.1\r\n" % path)
            s.write(b"Host: %s\r\n" % host)
            s.write(b"Connection: keep-alive\r\n")
            # Iterate over keys to avoid tuple alloc
            if cookies is not None:
                for cookie in cookies:
                    s.write(b"Cookie: ")
                    s.write(cookie)
                    s.write(b"=")
                    s.write(cookies[cookie])
                    s.write(b"\r\n")
            # End header
            s.write(b"\r\n")
            s.setblocking(False)
            self.s = s
        except Exception as e:
            s.close()
            self.s = None
            raise

    def close(self):
        self.chunked = False
        self.chunk_remain_size = 0
        self.chunk_reading = False
        self.last_event = ""
        if self.s != None:
            self.s.close()
        self.s = None
    
    def parse_header_gen(self):
        s = self.s
        # ---- read status line ----
        while True:
            l = s.readline()
            if l != None:
                break
            yield
        l = l.split(None, 2)
        status = int(l[1])
        if status != 200:
            self.close()
            raise Exception("http status is not 200.")
        # reason = ""
        # if len(l) > 2:
        #     reason = l[2].rstrip()
        # ---- read header ----
        while True:
            while True:
                l = s.readline()
                if l != None:
                    break
                yield
            # print('Received Headerdata %s' % l.decode('utf-8'))
            if not l or l == b"\r\n":
                break
            # ---- Header data ----
            if l.lower().startswith(b"transfer-encoding:"):
                if b"chunked" in l:
                    self.chunked = True
    
    def parse_header(self):
        for _ in self.parse_header_gen(): pass

    def body_readline(self):
        l = self.s.readline()
        if l == None:
            return None
        if self.chunked:
            if self.chunk_remain_size <= 0:
                # ---- skip tail \r\n ----
                if self.chunk_reading and self.chunk_remain_size == 0:
                    self.chunk_reading = False
                    return None
                # ---- read chunk size ----
                try:
                    self.chunk_remain_size = int(l.strip().decode("utf-8"), 16)
                except ValueError:
                    self.close()
                    raise OSError("Connection closed.")
                self.chunk_reading = True
                return None
            else:
                self.chunk_remain_size -= len(l)
                return l
        else:
            return l
    
    def fetch_event(self):
        l = self.body_readline()
        if l == None:
            return None
        if l.startswith(b":"):
            return None
        l = l.rstrip() # strip tail \r\n
        if l.startswith(b"event:"):
            self.last_event = l[6:].lstrip().decode("utf-8")
            return None
        elif l.startswith(b"data:"):
            if len(self.buffer) > 0:
                self.buffer.append(0x0A) # \n
            self.buffer.extend(l[5:].lstrip())
            return None
        elif len(l) == 0:
            text = self.buffer.decode("utf-8")
            event = self.last_event
            self.last_event = ""
            self.buffer = bytearray()
            if len(text) > 0:
                return event, text
            return None
