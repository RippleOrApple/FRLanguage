# 语言设计草案

本文档记录 FRLanguage 第一版语法草案。后续实现时可以根据复杂度继续调整。

## 文件扩展名

建议使用：

```txt
.fr
```

## 变量

```fr
let name = "FRLanguage";
let count = 3;
```

## 导入

```fr
import "helper.fr";
```

当前导入会执行目标文件，同一个文件只执行一次。导入路径必须是相对路径。

## 输出

```fr
print("hello");
print(1 + 2);
```

## 条件分支

```fr
if count >= 60 {
  print("pass");
} else {
  print("fail");
}
```

## 循环

```fr
let i = 0;

while i < 3 {
  print(i);
  i = i + 1;
}
```

跳出循环：

```fr
while true {
  break;
}
```

逻辑运算：

```fr
if count > 0 and count < 10 {
  print("small");
}

if count == 0 or count == 10 {
  print("edge");
}
```

## 赋值

```fr
let count = 1;
count = count + 1;
print(count);
```

## List

```fr
let items = [1, 2, 3];
print(items[0]);

items[1] = 42;
print(items);
```

## Map

```fr
let user = {"name": "FR", "version": 1};
print(user["name"]);

user["version"] = 2;
print(user);
```

## 内置函数

字符串处理：

```fr
let text = "hello";
print(len(text));
print(charAt(text, 1));
print(substring(text, 1, 4));
```

类型和转换：

```fr
print(type([1, 2]));
print(str(42) + "!");
print(number("41") + 1);
```

List 修改：

```fr
let items = [1];
push(items, 2);
print(pop(items));
```

文件读取：

```fr
let source = readFile("hello.fr");
print(source);
```

## 函数

```fr
fn add(a, b) {
  return a + b;
}

print(add(1, 2));
```

递归函数：

```fr
fn fact(n) {
  if n <= 1 {
    return 1;
  }

  return n * fact(n - 1);
}

print(fact(5));
```

## Future

第一版 Future 目标是学习异步模型，不追求真正并行。

```fr
fn delayValue(x) {
  return future {
    return x * 2;
  };
}

let value = await delayValue(21);
print(value);
```

## 设计取舍

- 第一版使用解释执行，不生成字节码。
- 第一版使用动态类型，不做静态类型检查。
- 第一版 Future 使用协作式调度，不做多线程。
- 第一版优先保证代码结构清楚，而不是追求性能。
