'''
自己搭建一个本地慢接口
'''
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class DelayHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(2)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"ok": true}')
    def log_message(self, format:str,*args)->None: 
        pass

print("慢接口就绪: http://127.0.0.1:8000/delay")
ThreadingHTTPServer(('127.0.0.1', 8000), DelayHandler).serve_forever()