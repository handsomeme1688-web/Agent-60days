print("---------Python变量的秘密--------")
a = 5
print(id(a))  # 输出一个地址，比如：140733194676112

a = a + 1
print(id(a))  # 输出一个完全不同的地址，比如：140733194676144

L = [1, 2]
print(id(L))  # 查看当前列表的地址

L.append(3)
print(id(L))  # 地址完全没有变！

print("---------Python函数可变参数--------")

def add_all(*numbers):
    print(type(numbers)) # <class 'tuple'>
    total = 0
    for n in numbers:
        total += n
    return total

# 你可以传任意个数字进去：
print(add_all(1, 2, 3))    # 输出: <class 'tuple'> 和 6
print(add_all(5, 10))      # 输出: <class 'tuple'> 和 15
print(add_all())           # 不传也行，输出: <class 'tuple'> 和 0

print("---------Python函数可变参数2--------")

def calc(numbers):
    sum = 0
    for n in numbers:
        sum = sum + n * n
    return sum
print(calc([1, 2, 3])) # 14

print(calc((1, 3, 5, 7))) # 84

def calc1(*numbers):
    sum = 0
    for n in numbers:
        sum = sum + n * n
    return sum
print(calc1(1, 2, 3)) # 14
nums = [1, 2, 3]
print(calc1(nums[0], nums[1], nums[2])) # 14


print("---------Python序列化--------")

import pickle
d = dict(name='Bob', age=20, score=88)
print(pickle.dumps(d))

print("--------`pickle.dump()`直接把对象序列化后写入一个file-like Object---------")
f = open('dump.txt', 'wb')
pickle.dump(d, f)
f.close()

print("--------`pickle.load()`从file-like Object中读取序列化后的对象---------")
f = open('dump.txt', 'rb')
d = pickle.load(f)
f.close()
print(d)

print("---------JSON--------")
import json
d = dict(name='Bob', age=20, score=88)
print(json.dumps(d)) # {"name":"Bob","age":20,"score":88}
print(type(json.dumps(d))) # <class 'str'>

json_str = '{"age": 20, "score": 88, "name": "Bob"}'
print(json.loads(json_str)) # 注意这里是json调用loads()方法，不是pickle
print(type(json.loads(json_str))) # <class 'dict'>

print("---------JSON与自定义类 --------")
import json

class Student(object):
    def __init__(self, name, age, score):
        self.name = name
        self.age = age
        self.score = score

def student2dict(std):
    return {
        'name': std.name,
        'age': std.age,
        'score': std.score
    }
s = Student('Bob', 20, 88)
print("student2dict: "+json.dumps(s, default=student2dict)+"数据类型"+str(type(json.dumps(s, default=student2dict))))
print("偷懒: "+json.dumps(s, default=lambda obj: obj.__dict__)+"数据类型"+str(type(json.dumps(s, default=lambda obj: obj.__dict__))))

def dict2student(d):
    return Student(d['name'], d['age'], d['score'])

json_str = '{"age": 20, "score": 88, "name": "Bob"}'
print(json.loads(json_str, object_hook=dict2student)) #<__main__.Student object at 0x000001FA4E807580>
