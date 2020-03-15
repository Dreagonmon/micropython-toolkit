from ssd1306desktop.ssd1306img import img1306
from PIL import Image
from binascii import b2a_base64

if __name__ == "__main__":
    img = Image.open("out/Veemon2.png")
    img2 = Image.new("1",(24,24),255)
    data = img.getdata()
    data2 = bytearray()
    for y in range(48):
        for x in range(48):
            if x%2!=0 or y%2!=0:
                continue
            color = data[y*48+x]
            data2.append(color[0])
    img2.putdata(data2)
    img2.show()
    data = img1306(img2)
    data = b2a_base64(data,newline=False)
    print(data.decode("ascii"))