'''Read and write PBM format image file
PBM format: http://netpbm.sourceforge.net/doc/pbm.html
Only support single image in a file
'''

def _is_space(char):
    r'''C isspace function'''
    return char in [0x20, 0x09 ,0x0a ,0x0b, 0x0c, 0x0d] #[ \t\n\v\f\r]

def _is_new_line(char):
    r''' char is \r or \n'''
    return char in [0x0a ,0x0d] #[\n\r]
def _is_comment_start(char):
    ''' char is #'''
    return char == 0x23 #[#]

def read_header(instream):
    r'''Read file header, get basic information
    :param: instream: stream that support seek, tell, read
    :returns: (
        width,
        hetght,
        raster_data_format_P1_or_P4_or_UNKNOWN,
        raster_start_position
    )
    '''
    # magic number
    instream.seek(0)
    mg = instream.read(2)
    if mg != b"P1" and mg != b"P4":
        return (-1, -1, b"UNKNOWN", -1)
    # state machine
    buffer = bytearray() # list to store bytes
    is_reading_info = False
    is_reading_comment = False
    width = -1
    height = -1
    byts = instream.read(1)
    while len(byts) == 1:
        char = byts[0]
        # reading comment state
        if is_reading_comment:
            if _is_new_line(char):
                is_reading_comment = False
        # reading info state
        elif is_reading_info:
            if _is_comment_start(char):
                is_reading_comment = True
            elif _is_space(char):
                if width < 0:
                    width = int(buffer.decode(),10)
                elif height < 0:
                    height = int(buffer.decode(),10)
                buffer = bytearray()
                is_reading_info = False
                if width >= 0 and height >= 0:
                    # read header finished
                    break
            else:
                buffer.append(char)
        # normal state
        elif not is_reading_info and not is_reading_comment:
            if _is_space(char):
                pass
            elif _is_comment_start(char):
                is_reading_comment = True
            else:
                buffer.append(char)
                is_reading_info = True
        byts = instream.read(1)
    pos = instream.tell()
    return (width, height, mg, pos)

def read_data(instream, width, height, format, offset=-1):
    r'''Read image data
    :param: instream: stream that support seek, tell, read
            width: image width
            height: image height
            format: b'P1' or b'P4'
    :return: data in MONO_HLSB format bytes
    '''
    if format != b"P1" and format != b"P4":
        return bytes(0)
    if offset >= 0:
        instream.seek(offset)
    width_count = width // 8
    bit_offset = width % 8
    if bit_offset != 0:
        width_count += 1
    size = width_count * height
    # bytecode format
    if format == b"P4":
        return bytearray(instream.read(size))
    # text format
    data = bytearray(size)
    bit = 0
    bitp = 0
    width_p = 0
    index = 0
    byts = instream.read(1)
    while index < size and len(byts) == 1:
        char = byts[0]
        if _is_space(char):
            pass
        else:
            bit = (bit << 1) | (char-0x30)
            bitp += 1
            width_p += 1
            if width_p == width:
                bit = bit << bit_offset
                data[index] = bit
                index += 1
                bit = 0
                bitp = 0
                width_p = 0
            elif (bitp >= 8):
                data[index] = bit
                index += 1
                bit = 0
                bitp = 0
        byts = instream.read(1)
    return data

def read_image(instream):
    r'''Read image file, return basic information and data
    :param: instream: stream that support seek, tell, read
    :returns: (
        width,
        hetght,
        raster_data_format_P1_or_P4_or_UNKNOWN,
        image_data
    )
    '''
    width, height, mg, _ = read_header(instream)
    data = read_data(instream, width, height, mg)
    return (width, height, mg, data)

def make_image(outstream, width, height, data, comment="made with bpm.py"):
    r'''Write an image file
    :param: file_path: file to write
            width: image width
            height: image height
            data: image data in MONO_HLSB format
    :return: file size
    '''
    outstream.write("P4\n# {:s}\n{:d} {:d}\n".format(comment, width, height).encode())
    outstream.write(data)
    outstream.write("\n".encode())
    size = outstream.tell()
    return size
