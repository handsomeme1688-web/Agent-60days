 
'''
如果服务器变慢了，你的 App 会不会卡死或者直接闪退。为了测试你的 App 质量过不过关，你需要人为制造一些“慢接口”来做压力测试。
 
① 用 https://httpbin.org/delay/2 模拟 10 个慢接口；② 同步循环请求一遍、 asyncio.gather
并发请求一遍；③ 打印两种方式总耗时对比（应约 20s vs 约 2s）。

'''
 
 
 
 
import asyncio
from typing import Callable
import httpx
import time

# URL='https://httpbingo.org/delay/2'
URL='http://127.0.0.1:8000/delay'

# 同步计时器
def timer(func:Callable)->Callable:
    def wrapper(*args,**kw):
        start_time=time.perf_counter()
        res = func(*args,**kw)
        end_time=time.perf_counter()
        past_time=end_time-start_time
        print(f'{func.__name__}运行了{past_time:.2f}')
        return res
    return wrapper

# 异步计时器
def async_timer(func:Callable)->Callable:
    async def wrapper(*args,**kw):
        start_time=time.perf_counter()
        res = await func(*args,**kw)
        end_time=time.perf_counter()
        past_time=end_time-start_time
        print(f'{func.__name__}运行了{past_time:.2f}')
        return res
    return wrapper

# 同步发送
@timer
def synchronous_send(n:int,url:str)->None:
    for _ in range(n):
        r=httpx.get(url,timeout=100.0)
        r.raise_for_status()
        print(r)

        
  
# 异步发送
async def asyncio_send(client:httpx.AsyncClient,url:str)->None:
    r= await client.get(url,timeout=100.0)
    r.raise_for_status()
    print(r)

@async_timer
async def run_asyn(url:str,n:int)->None:
    async with httpx.AsyncClient() as client:
        await asyncio.gather(*[asyncio_send(client,url) for _ in range(n)] )
        


    
def main()->None:
    print("--- 开始同步循环测试 ---")
    synchronous_send(10,URL)    
    print("--- 开始异步并发测试 ---")
    asyncio.run(run_asyn(URL,10))

    
    
if __name__ == '__main__':
    main()