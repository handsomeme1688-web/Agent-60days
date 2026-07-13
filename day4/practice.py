'''
任务《聊天机器人 v1》

要求：① 命令行多轮对话，自己维护 messages 历史列表；② /save 存档到 JSON、 /load 读
档、 /clear 清空；③ push。
'''

import json
from pathlib import Path
from typing import Any

from openai import OpenAI
import os
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from pydantic_settings import BaseSettings, SettingsConfigDict


FILE_PATH=Path(__file__).parent/"messages.json"

# pydantic 验证
class Settings(BaseSettings):
    # 定义需要从 .env 中读取的变量名
    deepseek_api_key:str
    deepseek_base_url:str
    
    model_config=SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra="ignore"
        
    )
    
# 实例化一个设置类
settings=Settings()


client=OpenAI(
    api_key=settings.deepseek_api_key,
    base_url=settings.deepseek_base_url
)


# 响应生成
def generate_response(messages:list)->ChatCompletion:
    response = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=messages,
        # reasoning_effort="high",
        # extra_body={'thinking':{'type':'enabled'}},
    )
    return response


# 处理用户输入数据
# 参数：用户原始输入的字符串
# 输出：message数据
def handle_user_input(user_raw:str)->dict:
    user_dict={"role":"user","content":user_raw}
    return user_dict


# 保存messages
# messages里面是混合数据
# 显式声明messages里可以是任何数据类型
def save_messages(filepath:Path,messages:list[Any])->None:
    # TODO 调用json序列化
    serializable_msg_list=[]
    for msg in messages:
        # hasattr(msg,'model_dump')用于检测遍历到的msg是否有model_dump方法，这是ChatCompletionMessage对象的方法
        if hasattr(msg,'model_dump'):
            serializable_msg={"role":msg.role,"content":msg.content}
            serializable_msg_list.append(serializable_msg)
        else:
            serializable_msg_list.append(msg)
    with open(filepath,'w',encoding='utf-8') as f:
        json.dump(serializable_msg_list,f,ensure_ascii=False,indent=2)




# 消息记录加载
def load_messages(filepath:Path)->list:
    with open(filepath,'r',encoding='utf-8') as f:
        data=json.load(f)
        return data
      
      
# 消息记录删除      
def clear_messages(filepath:Path)->None:
    with open(filepath,'w',encoding='utf-8') as f:
        json.dump([],f,ensure_ascii=False,indent=2)

    

# 消息数组新增
def add_new_message(messages:list,message:ChatCompletionMessage | dict)->None:
    messages.append(message)
    

def main()->None:
    
    # messages初始化
    messages=[
        {"role":"system","content":"You are a helpful assistant"},
    ]
    
    print('tips：使用 /load 读档; 使用 /save 存档并结束对话; 使用 /clear 清空\n>>>')
    
    while True:
        load_flag = input("")
        
        # 命令判断
        if load_flag=="/load":
            messages=load_messages(FILE_PATH)
            if messages:
                print(f"消息记录加载成功！{messages}")
                print(">>>")
                continue
            else:
                print("无历史消息记录！")
                continue
        if load_flag == "/save" :
            save_messages(FILE_PATH,messages)
            print(f'消息记录已经保存至{FILE_PATH}')
            return    
        if load_flag == "/clear" :
            clear_messages(FILE_PATH)
            print('消息记录已删除！')
            return
        
        # 添加用户消息
        user_dict=handle_user_input(load_flag)
        add_new_message(messages,user_dict)
        
        # LLM 输出，并等待用户下次输入
        message =  generate_response(messages).choices[0].message
        content=message.content
        print(content)
        print(">>>")
        
        # 添加模型消息
        add_new_message(messages,message)


if __name__ == "__main__":
    main()