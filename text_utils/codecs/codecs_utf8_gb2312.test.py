import sys, os
current_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(current_path, "..", "coding"))

try:
    from . import codecs_utf8_gb2312
except:
    import codecs_utf8_gb2312
import coding
from io import BytesIO

if __name__ == "__main__":
    dict_fp = open("codecs_utf8_gb2312.bin", "rb")
    codec = codecs_utf8_gb2312.Codecs(dict_fp)
    unicode = 23383
    gb2312 = codec.from_unicode(unicode)
    print(gb2312.decode("gb2312"))
    stream = BytesIO("你好中国".encode("utf8"))
    gb2312 = codec.from_stream(stream, 2)
    print(gb2312.decode("gb2312"))
    gb2312 = codec.from_string("中ew\r\nas国\new你we\r好we啊")
    print(gb2312.decode("gb2312"))
    stream = BytesIO(gb2312)
    reader = coding.GB2312Reader(stream)
    print(reader.readlines())