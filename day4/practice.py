'''
任务《聊天机器人 v1》

要求：① 命令行多轮对话，自己维护 messages 历史列表；② /save 存档到 JSON、 /load 读
档、 /clear 清空；③ push。
'''

import json
from pathlib import Path
from openai import OpenAI
from openai.types.chat import ChatCompletion
from pydantic_settings import BaseSettings, SettingsConfigDict


FILE_PATH=Path(__file__).parent/"messages.json"

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
def generate_response(messages:list)->ChatCompletion:
    response = client.chat.completions.create(
        model=settings.deepseek_model,
        messages=messages,
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
 

def main()->None:
    
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
        
        # LLM 输出，并等待用户下次输入
        message =  generate_response(messages).choices[0].message
        content=message.content or "" # or "" 是 Python 惯用法：content 有值就用它，是 None（或空串）就用 ""
        print(content)
        print(">>>")
        
        # 添加模型消息
        messages.append({"role": "assistant", "content": content})


if __name__ == "__main__":
    main()