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


FILE_PATH=Path(__file__).parent/"messages.json"

client=OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com"
)

# messages初始化
messages=[
    {"role":"system","content":"You are a helpful assistant"},
]

# 响应生成
def generate_response(messages:list)->ChatCompletion:
    response = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=messages,
        reasoning_effort="high",
        extra_body={'thinking':{'type':'enabled'}},
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
# 成功返回True，用于main输出保存的地址
# 显式声明messages里可以是任何数据类型
def save_messages(filepath:Path,messages:list[Any])->bool:
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
        # serializable_messages=[msg.model_dump() if hasattr(msg,'model_dump') else msg for msg in messages] 
        
    return True
  
# 消息记录加载
def load_messages(filepath:Path)->list:
    # if not os.path.exists(filepath) or os.path.getsize(filepath)==0:
    #         print("无消息记录！")
    #         return messages
    # else:
    with open(filepath,'r',encoding='utf-8') as f:
        data=json.load(f)
        return data
      
# 消息记录删除      
def clear_messages(filepath:Path)->bool:
    with open(filepath,'w',encoding='utf-8') as f:
        json.dump([],f,ensure_ascii=False,indent=2)
    return True
    
      
# json序列化
# 后期数据量如果很大，是不是需要考虑用异步IO？
# def json_write(filepath:str,messages:list)->None:
#     with open(filepath,'w') as f:
#         json.dump(messages,f)
    
# 消息数组新增
def add_new_message(messages:list,message:ChatCompletionMessage | dict)->None:
    messages.append(message)
    
    
    
    
def main()->None:
    global messages
    
    # TODO 初始化模型
    # client=OpenAI(
    #     api_key=os.environ.get('DEEPSEEK_API_KEY'),
    #     base_url="https://api.deepseek.com"
    # )
    
    # TODO 先不设置flag，默认用户通过终端退出。
    load_flag = input("tips：使用 /load 读档; 使用 /save 存档并结束对话; 使用 /clear 清空\n>>>")
    
    if load_flag=="/load":
        if load_messages(FILE_PATH):
            messages=load_messages(FILE_PATH)
            print(f"消息记录加载成功！{messages}")
        else:
            print("无历史消息记录！")
    if load_flag == "/save" :
        if save_messages(FILE_PATH,messages):
            print(f'消息记录已经保存至{FILE_PATH}')
            return    
    if load_flag == "/clear" :
        if clear_messages(FILE_PATH):
            print('消息记录已删除！')
            return
    
    user_dict=handle_user_input(load_flag)
    add_new_message(messages,user_dict)
    # TODO LLM输出问候语（包含两个命令的提示）,第一轮
    # 模型初始化完成
    # 返回 LLM 输出
    message =  generate_response(messages).choices[0].message
    content=message.content
    print(content)
    print(">>>")
    add_new_message(messages,message)
    while True:
        # TODO LLM输出问候语（包含两个命令的提示）,第一轮
        # 模型初始化完成
        # 返回 LLM 输出
        # message =  generate_response(messages).choices[0].message
        # content=message.content
        # print(content)
        # print(">>>")
        # TODO 模型的回复加入消息数组
        # add_new_message(messages,message)
        
        # TODO 用户输入需求 
        user_raw=input("")
        
        
        # TODO 用户输入处理成消息
        # user_dict=handle_user_input(user_raw)

        # TODO 加入消息数组
        # add_new_message(messages,user_dict)
        
        # TODO LLM做出响应并等待用户下次输入,回到了开头
        
        # TODO /save命令：把本轮对话存档到json，追加存档
        if user_raw == "/save" :
            if save_messages(FILE_PATH,messages):
                print(f'消息记录已经保存至{FILE_PATH}')
                return
        
        
        # TODO /clear 清空对话记录
        elif user_raw == '/clear':
            if clear_messages(FILE_PATH):
                print('成功删除消息记录！')
                return
        
        elif user_raw == '/load':
            print("对话过程中不能使用 /load 命令，请先保存并重启对话再使用此命令！")
            print('>>>')
            continue
        else:
        
                    
            # TODO 用户输入处理成消息
            user_dict=handle_user_input(user_raw)

            # TODO 加入消息数组
            add_new_message(messages,user_dict)
            
            # TODO LLM做出响应并等待用户下次输入,回到了开头
            
            message =  generate_response(messages).choices[0].message
            content=message.content
            print(content)
            print(">>>")
            # TODO 模型的回复加入消息数组
            add_new_message(messages,message)
            

        
        
        # TODO 最后要 push 到 github



if __name__ == "__main__":
    main()





















