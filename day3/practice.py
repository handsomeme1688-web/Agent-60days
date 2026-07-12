 
'''
如果服务器变慢了，你的 App 会不会卡死或者直接闪退。为了测试你的 App 质量过不过关，你需要人为制造一些“慢接口”来做压力测试。
 
① 用 https://httpbin.org/delay/2 模拟 10 个慢接口；② 同步循环请求一遍、 asyncio.gather
并发请求一遍；③ 打印两种方式总耗时对比（应约 20s vs 约 2s）。

'''
 
 
 
 
import asyncio
from typing import Callable
import httpx
import time

URL='https://httpbin.org/delay/2'

def timer(func:Callable)->Callable:
    def wrapper(*args,**kw):
        start_time=time.perf_counter()
        res = func(*args,**kw)
        end_time=time.perf_counter()
        past_time=end_time-start_time
        print(f'{func.__name__}运行了{past_time:.2f}')
        return res
    return wrapper

# 同步发送
@timer
def synchronous_send(n:int,url:str)->None:
    while n:
        n=n-1
        r=httpx.get(url,timeout=100.0)
        print(r)
  
# 异步
async def asyncio_send(url:str)->None:
    r=httpx.get(url,timeout=100.0)
    print(r)


async def run_asyn(url:str)->None:
    L = asyncio.gather(
        asyncio_send(url),
        asyncio_send(url),
        asyncio_send(url),
        asyncio_send(url),
        asyncio_send(url),
        asyncio_send(url),        
        asyncio_send(url),
        asyncio_send(url),
        asyncio_send(url),
        asyncio_send(url)
    )
    print(L)

    
def main()->None:
    print("--- 开始同步循环测试 ---")
    synchronous_send(10,URL)    
    
    print("\n-----------------------\n")
    print("--- 开始异步并发测试 ---")
    start_time=time.perf_counter()
    asyncio.run(run_asyn(URL))
    end_time=time.perf_counter()
    past_time=end_time-start_time
    print(f'异步并发运行了{past_time:.2f}')
    
    
if __name__ == '__main__':
    main()