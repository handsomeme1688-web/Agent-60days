'''
任务《简历抽取器》
要求：① 输入一段杂乱的自我介绍文本；② 输出 {姓名, 电话, 学历, 技能[]} ；③ 用 Pydantic 校验，
失败就把报错信息拼进 prompt 自动重试，最多 3 次。
'''

from functools import lru_cache
import json
from pathlib import Path
from openai.types.chat import ChatCompletion
from openai import OpenAI
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

FILE_PATH=Path(__file__).parent/"messages.json"

string="""
哈喽大家好，那个……被逼着来做个自我介绍。我叫张三（嗯对，就是那个法外狂徒的张三，但我是遵纪守法的）。
学历这块吧，说起来都是眼泪，本科在某某大学读的计算机科学与技术专业。
虽然拿到了学士学位，但感觉那四年我主要进修的是“如何优雅地在宿舍躺尸”以及“期末极限预习法律准备”。
至于技能……怎么说呢，我会的挺杂的。简历上写着精通 Python 和 Java，但实际上面对 Bug 时我主要靠“复制粘贴”和“对电脑拜拜”。
哦，我还考过一个大学英语六级（CET-6），目前的水平仅限于看美剧不用频繁盯着字幕，以及能听懂外国友人骂我。
噢对了，我 office 三件套玩得贼溜，尤其是 Excel，能用公式把一个简单的账单算得像高数现场。
如果你有什么急事（最好是别有事，尤其是工作），可以call我的电话：138-1234-5678。
不过我这人有轻度电话恐惧症，陌生号码一律当推销挂掉，所以强烈建议先发短信，或者直接加微信，备注一下你是谁。
差不多就这些了！一个普通的、每天都在为了生活对电脑疯狂输出的打工人。很高兴认识大家（如果你们不找我加班的话）！
"""

system_prompt = """
The user will provide some exam text. Please parse the "information" and "abstract" and output them in JSON format. 

EXAMPLE INPUT: 
哈喽大家好，那个……被逼着来做个自我介绍。我叫张三（嗯对，就是那个法外狂徒的张三，但我是遵纪守法的）。
学历这块吧，说起来都是眼泪，本科在清华大学读的计算机科学与技术专业。
虽然拿到了学士学位，但感觉那四年我主要进修的是“如何优雅地在宿舍躺尸”以及“期末极限预习法律准备”。
至于技能……怎么说呢，我会的挺杂的。简历上写着精通 Python 和 Java，但实际上面对 Bug 时我主要靠“复制粘贴”和“对电脑拜拜”。
哦，我还考过一个大学英语六级（CET-6），目前的水平仅限于看美剧不用频繁盯着字幕，以及能听懂外国友人骂我。
噢对了，我 office 三件套玩得贼溜，尤其是 Excel，能用公式把一个简单的账单算得像高数现场。
如果你有什么急事（最好是别有事，尤其是工作），可以call我的电话：138-1234-5678。
不过我这人有轻度电话恐惧症，陌生号码一律当推销挂掉，所以强烈建议先发短信，或者直接加微信，备注一下你是谁。
差不多就这些了！一个普通的、每天都在为了生活对电脑疯狂输出的打工人。很高兴认识大家（如果你们不找我加班的话）！
{"张三","138-1234-5678","清华大学本科",["英语六级","office"]}

EXAMPLE JSON OUTPUT:
{
    "information": "哈喽大家好，那个……被逼着来做个自我介绍。我叫张三（嗯对，就是那个法外狂徒的张三，但我是遵纪守法的）。学历这块吧，说起来都是眼泪，本科在清华大学读的计算机科学与技术专业。虽然拿到了学士学位，但感觉那四年我主要进修的是“如何优雅地在宿舍躺尸”以及“期末极限预习法律准备”。至于技能……怎么说呢，我会的挺杂的。简历上写着精通 Python 和 Java，但实际上面对 Bug 时我主要靠“复制粘贴”和“对电脑拜拜”。哦，我还考过一个大学英语六级（CET-6），目前的水平仅限于看美剧不用频繁盯着字幕，以及能听懂外国友人骂我。噢对了，我 office 三件套玩得贼溜，尤其是 Excel，能用公式把一个简单的账单算得像高数现场。如果你有什么急事（最好是别有事，尤其是工作），可以call我的电话：138-1234-5678。不过我这人有轻度电话恐惧症，陌生号码一律当推销挂掉，所以强烈建议先发短信，或者直接加微信，备注一下你是谁。差不多就这些了！一个普通的、每天都在为了生活对电脑疯狂输出的打工人。很高兴认识大家（如果你们不找我加班的话）！",
    "abstract": "{"张三","138-1234-5678","清华大学本科",["英语六级","office"]}"
}
"""

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
    skills : list
   
   
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


# 处理用户输入
def add_to_messages(str_raw:str)->dict:
    return {"role":"user","content":str_raw}


def main()->None:
    while True:
        messages:list[dict[str,str]]=[
            {"role":"system","content":system_prompt},
            # {"role":"user","content":string}
        ]
        
        # 获取输入
        raw_input=input("")
        
        # 输入处理，消息
        message=add_to_messages(raw_input)
        messages.append(message)
        
        # 消息传递给模型, 模型收到消息产生响应
        response=generate_response(messages)

        # TODO 输出json格式，try，最多3次
        n=3
        while n>0:
            n-=1
            content = response.choices[0].message.content
            if content:
                try:
                    # raw_str=content["abstract"]
                    # name,phone_number,edu_back,skills=content["abstract"]
                    # person-Person()
                    # TODO 期待模型输出为{姓名，电话，学历，技能[]}
                    # TODO 打印Person实例的json格式
                    # print(content)
                    print(json.loads(content))

                    break
                except json.JSONDecodeError as e:
                    e_str=str(e)
                    e_message=add_to_messages(e_str)
                    messages.append(e_message)
                    response=generate_response(messages)


if __name__ == "__main__":
    main()



