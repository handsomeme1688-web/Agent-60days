'''
任务《聊天机器人 v2》
要求：① 流式打字机输出；② 每轮结束打印本轮 token 数与累计费用（读 usage）；③ 历史超 3000
token 自动丢最早对话（保留 system；发送前用「字符数 ÷ 1.7」粗估即可）。
凭什么能做出来：①② 用今天学的流式与 usage；③ 用今天的 token 概念 + Day 4 的历史列表。
'''

import json
from pathlib import Path
from openai import OpenAI, Stream
from openai.types.chat import ChatCompletionChunk
from pydantic_settings import BaseSettings, SettingsConfigDict


FILE_PATH=Path(__file__).parent/"messages.json"
INPUT_PRICE_CACHED=0.025 / 1000000
INPUT_PRICE_NOT_CACHED=3 / 1000000
OUTPUT=6 / 1000000




# pydantic 验证
class Settings(BaseSettings):
    # 定义需要从 .env 中读取的变量名
    deepseek_api_key:str
    deepseek_base_url:str
    deepseek_model: str = "deepseek-v4-pro"
    
    model_config=SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra="ignore"
        
    )
    
# 实例化一个设置类
settings = Settings()  # type: ignore[call-arg]


client=OpenAI(
    api_key=settings.deepseek_api_key,
    base_url=settings.deepseek_base_url
)


# 响应生成
def generate_response(messages:list)->Stream[ChatCompletionChunk]:
    response = client.chat.completions.create(
        model=settings.deepseek_model,
        messages=messages,
        stream=True,
        stream_options={"include_usage": True},
    )
    return response


# 处理用户输入数据
# 参数：用户原始输入的字符串
# 输出：message数据
def handle_user_input(user_raw:str)->dict:
    user_dict={"role":"user","content":user_raw}
    return user_dict


# 保存messages
def save_messages(filepath:Path,messages:list[dict[str,str]])->None:
    with open(filepath,'w',encoding='utf-8') as f:
        json.dump(messages,f,ensure_ascii=False,indent=2)


# 消息记录加载
def load_messages(filepath:Path)->list:
    # 注意防止文件不存在
    if not filepath.exists():
        return []
    with open(filepath,'r',encoding='utf-8') as f:
        data=json.load(f)
        return data
      
      
# 消息记录删除      
def clear_messages(filepath:Path)->None:
    with open(filepath,'w',encoding='utf-8') as f:
        json.dump([],f,ensure_ascii=False,indent=2)


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

# 换算成token长度
def estimate_tokens(byte_number:float | int)->int :
    return int(byte_number/1.7)

    

# 历史超3000token自动丢最早对话
def drop(messages:list[dict],max_tokens:int)->tuple[list[dict],bool]:
    # 统计messages数组长度
    total_bytes=sum(len(msg["content"]) for msg in messages)
    total_tokens=estimate_tokens(total_bytes)
    
    # 计算system消息的大小
    system_bytes=len(messages[0]["content"])
    system_tokens=estimate_tokens(system_bytes)
    
    # 计算用户输入消息的大小
    user_bytes=len(messages[-1]["content"])
    user_tokens=estimate_tokens(user_bytes)
    
    # 太大直接禁止
    # 需要裁剪的前提是 total > 3000。而你的拒绝条件是 total > 3000 - system_tokens（比如 3000-16=2984）。**任何 > 3000 的数，必然也 > 2984。
    if user_tokens+system_tokens>max_tokens:
        return messages,False    
    
    # 适中，修剪(太小不会进入 while 循环)
    while total_tokens > max_tokens:
        # 成对删除
        delete_bytes=len(messages[1]["content"])+len(messages[2]["content"])
        delete_tokens=estimate_tokens(delete_bytes)
        messages.pop(1)
        messages.pop(1)
        # 更新总大小
        total_tokens-=delete_tokens
    return messages,True
        

def main()->None:
    total_tokens=0
    total_price=0
    max_tokens=3000
    # messages初始化
    messages:list[dict[str,str]]=[
        {"role":"system","content":"You are a helpful assistant"},
    ]
    
    print('tips：使用 /load 读档; 使用 /save 存档并结束对话; 使用 /clear 清空\n>>>')
    
    while True:
        user_raw = input("")
        
        # 命令判断
        if user_raw=="/load":
            messages=load_messages(FILE_PATH)
            if messages:
                print(f"消息记录加载成功！{messages}")
                print(">>>")
                continue
            else:
                print("无历史消息记录！")
                messages:list[dict[str,str]]=[{"role":"system","content":"You are a helpful assistant"},]
                print(">>>")
                continue
        if user_raw == "/save" :
            save_messages(FILE_PATH,messages)
            print(f'消息记录已经保存至{FILE_PATH}')
            return    
        if user_raw == "/clear" :
            clear_messages(FILE_PATH)
            print('消息记录已删除！')
            return
        
        # 添加用户消息
        user_dict=handle_user_input(user_raw)
        messages.append(user_dict)
        
        # 修剪
        messages,flag=drop(messages,max_tokens)
        if not flag:
            print("你的输入长度超限！请重新输入")
            print(">>>")
            continue
            
        
        # LLM 输出，并等待用户下次输入
        reasoning_content=''
        content=''
        final_usage = None 
        raw_response = generate_response(messages)
        for chunk in raw_response:
            delta_reasoning=chunk.choices[0].delta.reasoning_content # type: ignore
            if delta_reasoning:
                reasoning_content+=delta_reasoning
            delta_content=chunk.choices[0].delta.content 
            if delta_content:
                content+=delta_content
                print(delta_content,end='',flush=True)
            if hasattr(chunk,'usage') and chunk.usage is not None:
                final_usage=chunk.usage
                
        if final_usage:        
            delta_tokens,delta_price,total_tokens,total_price=usage(final_usage,total_tokens,total_price)
            print(f'\n本轮token数：{delta_tokens},花费{delta_price:.6f}元，累计花费{total_price:.6f}元')
        print("\n>>>")
        
        # 添加模型消息
        messages.append({"role": "assistant", "content": content})


if __name__ == "__main__":
    main()