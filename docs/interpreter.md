# 解释器说明

本文档记录 FRLanguage 第三阶段同步解释器的设计和当前支持范围。

## 职责

Interpreter 负责执行 Parser 生成的 AST。

处理流程：

```txt
源码 -> Token -> AST -> Interpreter -> 输出
```

当前解释器是树遍历解释器，不生成字节码。

## 当前支持的语句

变量声明：

```fr
let x = 1 + 2 * 3;
```

输出语句：

```fr
print(x);
```

表达式语句：

```fr
x + 1;
```

表达式语句会执行表达式，但不会输出结果。

代码块：

```fr
{
  let x = "inner";
  print(x);
}
```

while 循环：

```fr
while i < 3 {
  print(i);
  i = i + 1;
}
```

if 条件分支：

```fr
if score >= 60 {
  print("pass");
} else {
  print("fail");
}
```

函数声明和调用：

```fr
fn add(a, b) {
  return a + b;
}

print(add(1, 2));
```

future 和 await：

```fr
let value = await future {
  return 42;
};

print(value);
```

## 当前支持的表达式

字面量：

```fr
123
12.5
"hello"
true
false
```

变量读取：

```fr
x
```

List 字面量：

```fr
[1, 2, 3]
```

索引读取：

```fr
items[0]
```

变量赋值：

```fr
x = x + 1
```

索引赋值：

```fr
items[1] = 42
```

函数调用：

```fr
add(1, 2)
```

future 块：

```fr
future {
  return 42;
}
```

await 表达式：

```fr
await later()
```

括号表达式：

```fr
(1 + 2)
```

一元表达式：

```fr
-1
!false
```

二元表达式：

```fr
1 + 2
3 * 4
9 / 3
3 > 2
3 == 3
```

## 变量环境

变量保存在 `Environment` 中。

当前支持：

- 定义变量
- 读取变量
- 给已经存在的变量赋值
- 从外层环境读取变量
- 代码块局部作用域
- 未定义变量时报运行时错误

示例：

```fr
print(missing);
```

会报类似错误：

```txt
第 1 行，第 7 列：变量 missing 未定义
```

## List 模型

List 使用 Python 的 `list` 作为运行时表示。

当前支持：

- List 字面量
- 索引读取
- 索引赋值
- 输出 List

示例：

```fr
let items = [1, 2, 3];
items[1] = 42;
print(items);
```

输出：

```txt
[1, 42, 3]
```

索引必须是整数，越界会报运行时错误。

## 输出模型

解释器内部维护一个 `output` 列表。

执行：

```fr
print(1 + 2);
print(true);
```

会得到：

```python
["3", "true"]
```

命令行入口会把这些输出逐行打印到终端。

## 函数模型

函数声明会在当前环境中定义一个函数对象。

调用函数时：

- 创建一个新的局部环境
- 把参数名绑定到调用时传入的参数值
- 执行函数体
- 遇到 `return` 时立即结束函数并返回值
- 没有 `return` 时返回 `nil`

函数可以读取声明位置外层环境中的变量，因此递归调用可以工作。

## Future 和 Runtime 模型

当前 Future 使用最小 Runtime 任务队列。

执行 `future { ... }` 时：

- 创建一个 Future 对象
- 把 future 块加入 Runtime 任务队列
- 创建 Future 的当前代码继续执行
- 后续 `await` 这个 Future 时，Runtime 运行队列中的任务
- 任务遇到 `return` 时把返回值写入 Future
- 任务执行失败时把错误写入 Future

执行 `await` 时：

- 如果目标不是 Future，就报运行时错误
- 如果目标 Future 还没完成，就运行 Runtime 队列直到它完成
- 如果目标是已完成的 Future，就取出完成值
- 如果 Future 执行失败，就继续抛出错误

当前不会并行执行，也没有真正 IO 异步。

## 命令行入口

当前可以运行 `.fr` 文件：

```bash
$env:PYTHONPATH='src'; python -m frlang.main examples/hello.fr
```

## 当前限制

暂未支持并发执行、真正 IO 异步和暂停后恢复调用栈。当前 Runtime 是协作式任务队列。
