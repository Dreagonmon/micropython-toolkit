if __name__ == "__main__":
    import os, sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import pbm
    if len(sys.argv) < 2:
        sys.exit()
    file = sys.argv[1]
    fdir, name = os.path.split(file)
    name, ext = os.path.splitext(name)
    new_name = name + ".raw" + ext
    f = open(file,"rb")
    w,h,iformat,data = pbm.read_image(f)
    f.close()
    # with open(os.path.join(fdir,name+".log"),"wb") as f:
    #     f.write(data)
    # print(w,h,iformat,len(data))
    # for i in range(len(data)):
    #     b = data[i]
    #     if b != 0:
    #         print("index",i,"char",b)
    #         break
    f = open(os.path.join(fdir,new_name),"wb")
    pbm.make_image(f,w,h,data)
    f.close()