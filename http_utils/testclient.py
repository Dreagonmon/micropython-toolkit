import requests

data={"form":"aaaa"}

resp = requests.post("http://192.168.43.204:80/index.html",data=data)
print(resp.text)
while True:
    try:
        exec(input('> '))
    except :
        pass
input()