
import httpx


data = {'num': 123, 'flag': True}
# data 参数的结果都被封装成了字符串
r = httpx.post("https://httpbin.org/post", data=data,timeout=15.0)
print(r.text)
'''
{
  "args": {}, 
  "data": "", 
  "files": {}, 
  "form": {
    "flag": "true", 
    "num": "123"
  }, 
  "headers": {
    "Accept": "*/*", 
    "Accept-Encoding": "gzip, deflate, br, zstd", 
    "Content-Length": "17", 
    "Content-Type": "application/x-www-form-urlencoded", 
    "Host": "httpbin.org", 
    "User-Agent": "python-httpx/0.28.1", 
    "X-Amzn-Trace-Id": "Root=1-6a532201-5bef84375c947a1d13d3fdde"
  }, 
  "json": null, 
  "origin": "152.42.189.165", 
  "url": "https://httpbin.org/post"
}
'''


# json 参数的结果保留原数据类型
r = httpx.post("https://httpbin.org/post", json=data,timeout=15.0)
print(r.text)
'''
{
  "args": {}, 
  "data": "{\"num\":123,\"flag\":true}", 
  "files": {}, 
  "form": {}, 
  "headers": {
    "Accept": "*/*", 
    "Accept-Encoding": "gzip, deflate, br, zstd", 
    "Content-Length": "23", 
    "Content-Type": "application/json", 
    "Host": "httpbin.org", 
    "User-Agent": "python-httpx/0.28.1", 
    "X-Amzn-Trace-Id": "Root=1-6a532204-3115aa7521af813b38bd6e9a"
  }, 
  "json": {
    "flag": true, 
    "num": 123
  }, 
  "origin": "152.42.189.165", 
  "url": "https://httpbin.org/post"
}
'''
