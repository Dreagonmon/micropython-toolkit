import pbm

from io import BytesIO

pbm_image_file = '''P1
# test image
13 13
1 1 1 1 1 1 1 1 1 1 1 1 1
0 0 0 0 0 0 0 0 0 0 0 0 1
1 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 1 0 0 0 1
1 0 0 0 0 0 0 0 0 1 0 0 0
0 0 0 0 0 1 0 0 0 0 1 0 1
1 0 0 0 0 0 1 1 1 1 1 1 0
0 0 0 0 0 1 0 0 0 0 1 0 1
1 0 0 0 0 0 0 0 0 1 0 0 0
0 0 0 0 0 0 0 0 1 0 0 0 1
1 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 1
1 1 1 1 1 1 1 1 1 1 1 1 1
'''
output_file_path = "out.pbm"
if __name__ == "__main__":
    in_stream = BytesIO(pbm_image_file.encode("utf8"))
    width, height, format, data = pbm.read_image(in_stream)
    in_stream.close()
    print(width, height, format, data)
    with open(output_file_path, 'wb') as f:
        pbm.make_image(f, width, height, data, "P1")
    pass