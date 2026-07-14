'''
任务《简历抽取器》
要求：① 输入一段杂乱的自我介绍文本；② 输出 {姓名, 电话, 学历, 技能[]} ；③ 用 Pydantic 校验，
失败就把报错信息拼进 prompt 自动重试，最多 3 次。
'''

from functools import lru_cache
import json
from openai.types.chat import ChatCompletion
from openai import OpenAI
from pydantic import BaseModel, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

system_prompt =  """你是简历信息抽取助手。从用户提供的自我介绍中抽取信息，只输出 JSON，不要任何解释。
输出格式：
{"name": "姓名", "phone_number": "电话", "edu_back": "学历（如：某某大学本科）", "skills": ["技能1", "技能2"]}
要求：找不到的字段填空字符串或空数组，不要编造。"""


class Settings(BaseSettings):
    deepseek_api_key : str 
    deepseek_base_url : str
    deepseek_model : str = "deepseek-v4-pro"
    model_config=SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    
class Person(BaseModel):
    name : str
    phone_number : str
    edu_back : str
    skills : list[str]
   
   
# 延迟校验
@lru_cache
def get_settings()->Settings:
    return Settings() # type: ignore
    
    
# 延迟初始化客户端
@lru_cache
def get_client()->OpenAI:
    s=get_settings()
    return OpenAI(api_key=s.deepseek_api_key,base_url=s.deepseek_base_url)


# 生成响应
def generate_response(messages:list)->ChatCompletion:
    client=get_client()
    s=get_settings()
    response= client.chat.completions.create(
        model=s.deepseek_model,
        messages=messages,
        response_format={
            "type":"json_object"
        }
    )
    return response


def main()->None:
    while True:
        # 重建messages防污染
        messages:list[dict[str,str]]=[
            {"role":"system","content":system_prompt},
        ]
        
        # 获取输入
        raw_input=input("请输入简历：\n>>>").strip()
        if not raw_input:
            print("输入为空，请重新输入！")
            continue
        
        # 输入处理，消息
        message={"role":"user","content":raw_input}
        messages.append(message)
        
        # 消息传递给模型, 模型收到消息产生响应
        response=generate_response(messages)

        # 输出json格式，try，最多3次
        for _ in range(3):
            content = response.choices[0].message.content
            try:
                if not content:
                    raise ValueError("模型返回空内容")
                # pydantic校验
                person=Person.model_validate_json(content)
                
                # 打印Person实例的json格式
                print("\n",person.model_dump_json(indent=2),'\n')
                break
            except (json.JSONDecodeError,ValidationError,ValueError) as e:
                # 三类失败统一处理：空内容 / JSON 语法错 / 字段校验错 → 均带着错误原因重试
                messages.append({"role":"assistant","content":content or "(空)"}) 
                messages.append({"role":"user","content":f'你的输出有误{e}'})
                response=generate_response(messages)
        else:
            print("重试三次仍然失败")


if __name__ == "__main__":
    main()



