'''
任务《聊天机器人 v3：会用工具》
要求：① 接 2 个真工具——查天气（wttr.in：浏览器/代码访问 https://wttr.in/城市名 即可拿数据；备
选和风天气 https://dev.qweather.com ）+ 计算器（安全的四则运算）；② 完整实现 tool call 循环：模
型返回 tool_calls → 你执行 → 结果以 tool 角色塞回 → 模型给最终回答；③ 支持一次触发多个工具。
'''



from functools import lru_cache
import json
from pathlib import Path

import httpx
from openai import OpenAI, Stream
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


FILE_PATH=Path(__file__).parent/"messages.json"
INPUT_PRICE_CACHED=0.025 / 1000000
INPUT_PRICE_NOT_CACHED=3 / 1000000
OUTPUT=6 / 1000000

class Settings(BaseSettings):
    deepseek_api_key : str
    deepseek_base_url : str
    deepseek_model :str ="deepseek-v4-pro"
    model_config=SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    

# 设置实例化
@lru_cache
def get_settings()->Settings:
    return Settings() # type: ignore


# 客户端
@lru_cache
def get_client()->OpenAI:
    s=get_settings()
    return OpenAI(api_key=s.deepseek_api_key,base_url=s.deepseek_base_url)

# 生成响应，流式
def get_stream_response(messages:list)->Stream[ChatCompletionChunk]:
    client=get_client()
    s=get_settings()
    response=client.chat.completions.create(
        model=s.deepseek_model,
        messages=messages,
        tools=tools, # type: ignore
        stream=True,
        stream_options={"include_usage":True}
    ) # type: ignore
    return response

# 生成响应，阻塞式
def get_block_response(messages:list)->ChatCompletion:
    client=get_client()
    s=get_settings()
    response=client.chat.completions.create(
        model=s.deepseek_model,
        messages=messages,
        tools=tools, # type: ignore
    ) # type: ignore
    return response

# 查天气
def get_weather(location:str)->dict:
    r=httpx.get(f"https://wttr.in/{location}?format=j1")
    data= r.json()
    current=data["current_condition"][0]
    current_weather=current["weatherDesc"][0]["value"]
    current_temp_c=current["temp_C"]
    current_temp_f=current["temp_F"]
    return {"location":location,"weather":current_weather,"temp_c":current_temp_c,"tem_f":current_temp_f}

# 四则运算,参数必须匹配
def calculate(first_number: float, second_number: float, operator: str) -> float | None:
    match operator:
        case "+":
            return first_number+second_number
        case "-":
            return first_number-second_number
        case "*":
            return first_number*second_number
        case "/":
            if second_number != 0:
                return first_number/second_number
            else:
                print("NaN!0不能作为除数！")
                return 

# 工具映射
available_functions={
    "get_weather":get_weather,
    "calculate":calculate
}
        
# tool定义
tools=[
    {
        "type":"function",
        "function":{
            "name":"get_weather",
            "description":"Get weather of a location, the user should supply a location first.",
            "parameters":{
                "type":"object",
                "properties":{
                    "location":{
                        "type":"string",
                        "description":"The city, e.g. San Francisco"
                    }
                },
                "required":["location"]
            }
        }
    },
    {
        "type":"function",
        "function":{
            "name":"calculate",
            "description":"Get result of calculation of two number, the user should supply two number and the operator first.",
            "parameters":{
                "type":"object",
                "properties":{
                    "first_number":{
                        "type":"number",
                        "description":"The first number, e.g. 2334.3"
                    },
                    "second_number":{
                        "type":"number",
                        "description":"The second number, e.g. 7.3"
                    },
                    "operator":{
                        "type":"string",
                        "description":"The operator for two the number, you can choose '+' or '-' or '*' or '/' according to the user's demand. e.g. if the user want to calculate a/b, and you should choose '/'"
                    }
                },
                "required":["first_number","second_number","operator"]
            }
        }
    }
]

# 消息记录持久化
def save(filepath:Path,messages:list)->None:
    with open(filepath,'w',encoding='utf-8') as f:
        json.dump(messages,f,ensure_ascii=False,indent=2)
    
    
# 消息记录加载
def load(filepath:Path)->list:
    if not filepath.exists():
        return []
    with open(filepath,'r',encoding='utf-8') as f:
        data=json.load(f)
        return data


# 消息记录删除
def clear(filepath:Path)->None:
    with open(filepath,'w',encoding="utf-8") as f:
        json.dump([],f,ensure_ascii=False,indent=2)
        

# token换算
def to_token(bytes_number:float|int)->int:
    return int(bytes_number/1.7)
    


# 计算开销
def usage(final_usage,total_tokens,total_price)->tuple[int,float,int,float]: 
    input_cached=final_usage.prompt_tokens_details.cached_tokens
    output=final_usage.completion_tokens
    total_input=final_usage.prompt_tokens
    delta_price=input_cached*INPUT_PRICE_CACHED+OUTPUT*output+(total_input-input_cached)*INPUT_PRICE_NOT_CACHED
    delta_tokens=total_input+output
    total_tokens+=delta_tokens
    total_price+=delta_price
    return delta_tokens,delta_price,total_tokens,total_price
    

# TODO token滑动窗口
def drop(messages:list,max_tokens:int)->tuple[list[dict],bool]:
    # 统计messages数组长度
    total_bytes = sum(len(msg["content"]) for msg in messages)
    total_tokens = to_token(total_bytes)
    
    # 计算system消息的大小
    system_bytes = len(messages[0]["content"])
    system_tokens = to_token(system_bytes)
    
    # 计算用户/工具输入的大小
    user_bytes=len(messages[-1]["content"])
    user_tokens=to_token(user_bytes)
        
    # 太大直接禁止
    if user_tokens + system_tokens>max_tokens:
        return messages,False
    
    while total_tokens>max_tokens:
        delete_bytes=len(messages[1]["content"])
        delete_tokens=to_token(delete_bytes)
        if messages[1]["role"] in  ["user","assistant"]:
            messages.pop(1)
        total_tokens-=delete_tokens
    return messages,True


# TODO 主函数
def main()->None:
    # 总tokens
    total_tokens=0
    
    # 总金额
    total_price=0
    
    # 窗口最大
    max_tokens=1000000
    # messages初始化
    messages=[
        {"role":"system","content":"You are a helpful assistant"}
    ]
    print('tips：使用 /load 读档; 使用 /save 存档; 使用 /clear 清空; 使用 /exit 自动保存并结束对话\n')
    while True:
        user_raw=input("\n>>>")
        if user_raw=="/load":
            messages=load(FILE_PATH)
            if messages:
                print(f"消息加载成功！{messages}")
                continue
            else:
                print("无历史消息记录！")
                continue
        
        if user_raw=="/save":
            save(FILE_PATH,messages)
            print("消息记录保存成功！")
            continue
            
        if user_raw=="/clear":
            clear(FILE_PATH)
            print("消息记录已经删除！")
            continue
        
        if user_raw=="/exit":
            save(FILE_PATH,messages)
            print("消息记录保存成功,再见！")
            exit(0)
            
        # 添加用户消息
        messages.append({"role":"user","content":user_raw})
        
        # 修剪
        messages,flag = drop(messages,max_tokens)
        if not flag:
            print("你的输入长度超限！请重新输入")
            continue
        
        # 获取模型回答
        content = ""
        tool_call_chunks=[]
        final_usage=None
        is_tool_call=False
        
        # 第一次回答用于判断是否需要调用工具 
        first_answer = get_block_response(messages)
        message=first_answer.choices[0].message
        
        # 如果需要调用工具
        if message.tool_calls : 
            messages.append({"role":"assistant","content":message.content})
            for tool in message.tool_calls:
                func_name=tool.function.name # type: ignore
                func_args=json.loads(tool.function.arguments) # type: ignore
                
                if func_name in available_functions:
                    result=available_functions[func_name](**func_args)
                    messages.append(
                        {
                            "role":"tool",
                            "name":func_name,
                            "content":str(result)
                            }
                        )

            second_answer=get_stream_response(messages)
            for chunk in second_answer:
                delta_content=chunk.choices[0].delta.content
                if content:
                    print(delta_content,end='',flush=True)
                    content+=delta_content
                
            messages.append({"role":"assistant","content":content})    
        
        else:
            messages.append({"role":"assistant","content":content})
            print("\n",message.content)
        
        # for chunk in first_answer:
        #     delta=chunk.choices[0].delta
            
        #     # 如果需要调用工具，就不打印任何信息
        #     if delta.tool_calls:
        #         # 不是所有chunk都带有tool_call，第一块有就不允许后面的输出
        #         is_tool_call=True
        #         tool_calls.append(delta.tool_calls)
        #         continue
            
        #     #不调用工具，直接打印
        #     if not is_tool_call and delta.content:
        #         content += delta.content
        #         print(delta.content,end='',flush=True)
                
        #     # 本轮结束
        #     if hasattr(chunk,"usage") and chunk.usage is not None:
        #         final_usage = chunk.usage
        #         delta_tokens,delta_price,total_tokens,total_price=usage(final_usage,total_tokens,total_price)
        #         print(f'\n本轮token数：{delta_tokens},花费{delta_price:.6f}元，累计花费{total_price:.6f}元')
        #         # 
        #         messages.append({"role":"assistant","content":content})   
                
        # if is_tool_call:  
        #     # 把tool call碎片复原
        #     tool_calls=get_tool_calls(tool_call_chunks)
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
        #     # 第二次回答说人话
        #     final_answer = get_stream_response(messages)
        #     for chunk in final_answer:
        #         delta_content=chunk.choices[0].delta.content
        #         if delta_content:
        #             content+=delta_content
        #             print(delta_content,end='',flush=True)
                    
        #         if hasattr(chunk,"usage") and chunk.usage is not None:
        #             final_usage = chunk.usage
        #             delta_tokens,delta_price,total_tokens,total_price=usage(final_usage,total_tokens,total_price)
        #             print(f'\n本轮token数：{delta_tokens},花费{delta_price:.6f}元，累计花费{total_price:.6f}元')
        #             # 添加模型消息
        #             messages.append({"role":"assistant","content":content})    
                    
            
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    # print(get_weather("New York"))
    


if __name__ =="__main__":
    main()



























