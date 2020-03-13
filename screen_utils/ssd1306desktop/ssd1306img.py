#-*- coding:utf-8 -*-
from PIL import Image,ImageFilter,ImageFont,ImageDraw
from typing import Union

# convert image to black-white
def bwimg(img:Image):
    '''将图片转成黑白两种颜色的'''
    img = img.convert("1")
    return img

# resize image but keep w:h
def fitimg(img:Image,maxw:int=128,maxh:int=64):
    '''缩放图像，保持比例'''
    r1 = maxw/maxh
    r2 = img.width/img.height
    if r1 > r2:
        maxw = int(maxh*img.width/img.height)
    else :
        maxh = int(maxw*img.height/img.width)
    img = img.resize((maxw,maxh))
    return img

# get black-white border image
def contourimg(img:Image):
    '''提取图片边界'''
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
def saveimg(img:Image,path:str,iformat:str):
    '''保存图片'''
    img.save(path,iformat)

# convert image bytes for ssd1306.
def img1306(img:Image,invert:bool=False):
    '''将图片转换成ssd1306用的格式的字节流，MONO_VLSB格式'''
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
def emu1306(data:Union[bytearray,bytes,list],width:int,height:int,invert:bool=False):
    '''使用ssd1306格式的图片数据生成图像'''
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
def fontfile(fontpath:str,size:int):
    '''从指定字体文件加载指定大小的字体文件'''
    return ImageFont.truetype(fontpath,size)

# draw char as image
def fontimg(ch:str,font:ImageFont,width:int,height:int):
    '''绘制一个文字，用于生成字库'''
    img = Image.new("1",(width,height),color=255)
    dr = ImageDraw.Draw(img)
    dr.text((0,0),ch,font=font)
    return img