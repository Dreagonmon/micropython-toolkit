from bottle import route,post,run,static_file,request
@post("/<filename:path>")
def static_rt(filename):
    forms = request.forms
    for k in forms.keys():
        print(k,forms[k])
    return filename

run(host="0.0.0.0",port=8080)
input()