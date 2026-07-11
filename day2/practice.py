'''
任务《通讯录 v2》
要求：① 全部函数加类型注解；② 联系人改用 Pydantic 模型，校验手机号 11 位、邮箱含 @，非法输入
给出人话报错；③ 写一个 @timer 装饰器，打印每个命令耗时。

'''



import time
from typing import Annotated, Callable
from pydantic import BaseModel, StringConstraints, TypeAdapter, ValidationError
import json
import os
from pathlib import Path



#类型别名
Phone=Annotated[str,StringConstraints(pattern=r'^1\d{10}$')]
Email=Annotated[str,StringConstraints(pattern=r'.+@.+')]

#质检，使用同一份规则
phone_adapter=TypeAdapter(Phone)
email_adapter=TypeAdapter(Email)


# 定义Pydantic类
class Contact(BaseModel):
    name : str
    phone : Phone
    email : Email
    remark : str
    
    
# 定义装饰器
def timer(func:Callable)->Callable:
    def wrapper(*args,**kw):
        start_time=time.perf_counter()
        res=func(*args,**kw)
        end_time=time.perf_counter()
        past=end_time-start_time
        print(f"函数{func.__name__}运行了{past:.4f}秒")
        return res
    return wrapper
        
        
# 判断是否有效
def ask_valid(prompt:str,adapter:TypeAdapter,tip:str)->str:
    while True:
        try:
            return adapter.validate_python(input(prompt))
        except ValidationError:
            print(f"格式不对：{tip}")
        
    
    

    
# 类型转换
def Contact2dict(contact:Contact)->dict:
    return {
        "name":contact.name,
        "phone":contact.phone,
        "email":contact.email,
        "remark":contact.remark
    }

def dict2Contact(d:dict)->Contact | None:
    try:
        contact=Contact(**d)
        return contact
    except ValidationError as e:
        print(e)
        
            
    

# 指定要修改的文件
file=Path(__file__).parent/"contacts.json"

# 加载数据
def load_data(filename:Path)->list:
    # 若文件为空或路径不存在
    if not Path(filename).exists() or os.path.getsize(filename)==0:
        save_data([],filename)
        return []
    with open(filename,'r',encoding="utf-8") as f:
        data_list=json.load(f)
        return data_list


# 保存数据
def save_data(data_list:list,filename:Path)->None:
    with open(filename,'w',encoding='utf-8') as f:
        json.dump(data_list,f,ensure_ascii=False,indent=2)

# 查 
@timer
def find_by_name(name:str,filename:Path=file)->dict:
    data_all=load_data(filename)
    if data_all ==[]:
        return {}
    for data in data_all:
        if data["name"]==name:
            return data
    return {}

#查所有
@timer
def list_all(filename:Path=file)->list:
    data_list=load_data(filename)
    if data_list==[]:
        return []
    return data_list


# 删
@timer
def delete_by_name(name:str,filename:Path=file)-> bool:
    if not find_by_name(name,filename):
        return False
    # 获取所有数据
    data_list=load_data(filename)
    # 删掉匹配项
    data_list=[d for d in data_list if d["name"]!=name]
    
    # 重新写入
    save_data(data_list,filename)
    return True

#删全部
@timer
def deleteAll(flag:str,filename:Path =file)-> bool:
    if flag=='y': 
        save_data([],file)
        return True
    return False

# 改
@timer
def update(contact:Contact,filename:Path=file)->bool:
    data_list =load_data(filename)
    for d in data_list:
        if d["name"]== contact.name:
            d["phone"]=contact.phone
            d["email"]=contact.email
            d["remark"]=contact.remark
            break
    save_data(data_list,filename)
    return True
    

# 增，append
# 新建一个Contact类对象--> 打开文件,反序列化后读取数据--> 查询文件中是否已存在 --> 存在则返回，新增失败 --> 不存在转成dict --> 序列化为json --> 存入文件 --> close就能写入磁盘
@timer
def add(contact:Contact,filename:Path)->bool:
    data_list = load_data(filename)
    
    # 1. 业务规则把关：在已有的数据中检查是否重名
    # 假设你的 data_list 里面存的是字典，通过 ['name'] 获取名字
    for item in data_list:
        if item.get("name") == contact.name:
            return False  # 重名了，添加失败，直接返回 False
        
    data_list.append(Contact2dict(contact))
    save_data(data_list,filename)
    return True



def main()->None:
    
    # 这里放你程序的核心业务逻辑
    flag=True
    while(flag):
        print("---------通讯录管理系统---------")
        print("新增联系人，请输入：1")
        print("删除联系人，请输入：2")
        print("修改联系人，请输入：3")
        print("查询联系人，请输入：4")
        print("清空联系人，请输入：5")
        print("查询所有联系人，请输入：6")
        print("退出系统，请输入：0")
        print("------------------------------")

        index=input("")
        match index:
            case "1":
                name=input('请输入你要新增的联系人姓名：')
                phone=ask_valid("电话号码：",phone_adapter,"电话号码必须是11位数字，且以数字1开头！")
                email=ask_valid("邮箱：",email_adapter,"邮箱必须包含'@'符号！")
                remark=input("请输入备注：")
                contact=Contact(name=name,phone=phone,email=email,remark=remark)
                if add(contact, file):
                    print("新增成功！")
                else:
                    print("新增失败！联系人已存在！")
            case "2":
                name=input("请输入你要删除的联系人姓名：")
                if not delete_by_name(name):  
                    print("联系人不存在或通讯录为空")
                else:
                    print("删除成功！")
            case "3":
                name=input("请输入你要修改的联系人姓名：")
                if not find_by_name(name,file):
                    print("联系人不存在或通讯录为空")
                    continue
                # 电话和邮箱分开检查
                phone=ask_valid("电话号码：", phone_adapter,"电话号码必须是11位数字，且以数字1开头！")
                email=ask_valid("邮箱：", email_adapter,"邮箱必须包含'@'符号！")
                remark=input("备注：")
                contact=Contact(name=name,phone=phone,email=email,remark=remark)
                if update(contact):
                    print("修改成功！")
            case "4":
                name=input("请输入你要查询的联系人姓名：")
                print(find_by_name(name))
            case '5':
                confirm=input("此操作会删除所有联系人，请再次确认！(y/n)")
                if deleteAll(confirm,file):
                    print("删除成功！")
            case '6':
                print(list_all(file))
            case "0":
                flag=False
                exit()
            case _:
                print("非法输入！请重新输入！")
    

if __name__ == "__main__":
    main()
