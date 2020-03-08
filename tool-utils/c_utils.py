from json import load,dump
cfg = {}
def init():
    global cfg
    try:
        with open('/boot.cfg','rb') as f:
            cfg = load(f)
    except Exception as e:
        print('config load failed!')
        from sys import print_exception
        print_exception(e)
        cfg = {}
    print(cfg)
def set(key,value):
    global cfg
    cfg[key] = value
    f = open('/boot.cfg','wb')
    dump(cfg,f)
    f.close()
    #print('config saved')
    #print(cfg)
def get(key,default=None):
    global cfg
    if key in cfg:
        return cfg[key]
    else:
        return default
def get_int(key,default=None):
    global cfg
    if key in cfg:
        try :
            return int(cfg[key])
        except:
            return default
    else:
        return default
def set_boot_cmd(cmd):
    set('start_cmd',cmd)