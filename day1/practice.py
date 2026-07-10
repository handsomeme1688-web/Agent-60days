'''
练（2.5h）【独立完成】 
写「命令行通讯录」：用一个 Contact 类 + JSON 文件持久化，支持增/删/查/列出。写完 commit。
'''

from fileinput import filename
import json
import os
from pathlib import Path

class Contact:
    def __init__(self,name,phone,remark):
        self.name=name
        self.phone=phone
        self.remark=remark

def Contact2dict(contact):
    return {
        "name":contact.name,
        "phone":contact.phone,
        "remark":contact.remark
    }

def dict2Contact(d):
    return Contact(d["name"],d["phone"],d["remark"])

# 指定要修改的文件
file="./day1/contact.txt"


def load_data(filename):
    # 若文件为空或路径不存在
    if not Path(filename).exists() or os.path.getsize(filename)==0:
        with open(filename,'w',encoding='utf-8') as f:
            json.dump([],f)
        return []
         


    with open(filename,'r',encoding="utf-8") as f:
        data_list=json.load(f)
        return data_list

# 查
def find(name,filename=file):
    if load_data(filename) ==[]:
        print("通讯录为空")
        return False
    for data in load_data(filename):
        if data["name"]==name:
            print(data)
            return True
    print("无此联系人！")
    return False

# 删
def deleteByName(name,filename=file):
    if not find(name,filename):
        return "联系人不存在或通讯录为空"
    # 获取所有数据
    data_list=load_data(filename)
    # 删掉匹配项
    data_list=[d for d in data_list if d["name"]!=name]
    
    # 重新写入
    with open(filename,'w',encoding='utf-8') as f:
        json.dump(data_list,f)
    print("删除成功！")


def deleteAll(filename=file):
    flag=input("此操作会删除所有联系人，请再次确认！(y/n)")
    if flag=='y': 
        
        with open(filename,'w',encoding='utf-8') as f:
            print("通讯录已清空！")
            pass
    else:
        return

# 改
def update(name,filename=file):

    if not find(name,filename):
        return "联系人不存在或通讯录为空"
    
    phone=input("此人的电话：")
    remark=input("备注：")

    data_list =load_data(filename)
    for d in data_list:
        if d["name"]== name:
            d["name"]=name
            d["phone"]=phone
            d["remark"]=remark
        print("修改成功！", d)
        break
    with open(filename,'w',encoding='utf-8') as f:
        json.dump(data_list,f)
    return 
    

# 增，append
# 新建一个Contact类对象--> 打开文件,反序列化后读取数据--> 查询文件中是否已存在 --> 存在则返回，新增失败 --> 不存在转成dict --> 序列化为json --> 存入文件 --> close就能写入磁盘
def add(filename):
    data_list=load_data(filename)
    

    name=input('请输入联系人姓名：')
    for d in data_list:
        if d["name"]==name:
            print("新增失败！联系人已存在："+ d)
            return 
    phone=input("请输入电话：")
    remark=input("请输入备注：")
    contact=Contact(name,phone,remark)
    data_list.append(Contact2dict(contact))
    with open(filename,'w',encoding='utf-8') as f:
        json.dump(data_list,f)
    print("新增成功！")

def main():
    # 这里放你程序的核心业务逻辑
    flag=True
    while(flag):
        print("---------通讯录管理系统---------")
        print("新增联系人，请输入：1")
        print("删除联系人，请输入：2")
        print("修改联系人，请输入：3")
        print("查询联系人，请输入：4")
        print("清空联系人，请输入：5")
        print("退出系统，请输入：0")
        print("------------------------------")

        index=input("")
        match index:
            case "1":
                add(file)
            case "2":
                name=input("请输入你要删除的联系人姓名：")
                deleteByName(name)
            case "3":
                name=input("请输入你要修改的联系人姓名：")
                update(name)
            case "4":
                name=input("请输入你要查询的联系人姓名：")
                find(name)
            case '5':
                deleteAll(file)
            case "0":
                flag=False
                exit()
            case _:
                print("非法输入！请重新输入！")
    

if __name__ == "__main__":
    main()
