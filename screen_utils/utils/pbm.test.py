import pbm

from io import BytesIO

pbm_image_file = '''P1
# Hello Dragon
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
    # in_stream = BytesIO(pbm_image_file.encode("utf8"))
    in_stream = open(output_file_path, 'rb')
    width, height, format, data, comment = pbm.read_image(in_stream)
    print(comment)
    in_stream.close()
    print(width, height, format, data)
    with open(output_file_path, 'wb') as f:
        pbm.make_image(f, width, height, data, "P1", comment)
    pass