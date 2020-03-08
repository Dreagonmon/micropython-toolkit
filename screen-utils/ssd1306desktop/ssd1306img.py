#-*- coding:utf-8 -*-
from PIL import Image,ImageFilter,ImageFont,ImageDraw

# convert image to black-white
def bwimg(img):
    img = img.convert("1")
    return img

# resize image but keep w:h
def fitimg(img,maxw=128,maxh=64):
    r1 = maxw/maxh
    r2 = img.width/img.height
    if r1 > r2:
        maxw = int(maxh*img.width/img.height)
    else :
        maxh = int(maxw*img.height/img.width)
    img = img.resize((maxw,maxh))
    return img

# get black-white border image
def contourimg(img):
    img = (img
        .convert("L")
        .filter(ImageFilter.SMOOTH_MORE)
        .filter(ImageFilter.CONTOUR)
        .filter(ImageFilter.SMOOTH_MORE)
        .filter(ImageFilter.EDGE_ENHANCE_MORE)
        .filter(ImageFilter.SMOOTH_MORE)
        .filter(ImageFilter.SHARPEN)
        .convert("1")
        )
    return img

# save a image to path with format
def saveimg(img,path,iformat):
    img.save(path,iformat)

# convert image bytes for ssd1306.
def img1306(img,invert=False):
    img = img.convert("1")
    # ensure image`s height (h%8==0)
    if not img.height%8 == 0:
        nh = img.height//8 + 1
        nimg = Image.new("1",(img.width,nh))
        img = nimg.paste(img,(0,0,img.width,img.height))
        img.load()
    # the number of lines
    rows = img.height//8
    # buffer
    buf = img.getdata()
    data = []
    for row in range(rows):
        for col in range(img.width):
            byt = 0x00
            for bit in range(7,-1,-1):
                # parse byte
                y = row*8 + bit
                pos = y*img.width + col
                # black as image data
                if (buf[pos]==0) ^ invert:
                    byt = byt | 0x01
                if bit > 0:
                    # not last bit
                    byt = byt << 1
            data.append(byt)
    return bytearray(data)

# ssd1306 bytes to img
def emu1306(data,width,height,invert=False):
    if invert:
        buf = bytearray([0x00]*width*height)
    else:
        buf = bytearray([0xff]*width*height)
    rows = height//8
    
    for row in range(rows):
        for col in range(width):
            for bit in range(7,-1,-1):
                # parse byte
                y = row*8 + bit
                pos = y*width + col
                pat = 0x01 << bit
                # print(row*width + col)
                if data[row*width + col] & pat > 0:
                    if invert:
                        buf[pos] = 0xff
                    else:
                        buf[pos] = 0x00
    # print(buf)
    img = Image.new("1",(width,height))
    img.putdata(buf)
    return img

# load truetype font from file
def fontfile(fontpath,size):
    return ImageFont.truetype(fontpath,size)

# draw char as image
def fontimg(ch,font,width,height):
    size = font.getsize(ch)
    img = Image.new("1",size,color=255)
    dr = ImageDraw.Draw(img)
    dr.text((0,0),ch,font=font)
    return img