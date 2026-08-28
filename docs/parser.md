# 语法分析器说明

本文档记录 FRLanguage 第二阶段 Parser 的设计和当前支持范围。

## 职责

Parser 负责把 Token 列表转换成 AST。

处理流程：

```txt
Token 列表 -> 递归下降解析 -> AST
```

Parser 不负责执行代码，也不负责计算表达式结果。它只负责判断 Token 是否能组成合法语法结构。

## 当前支持的语句

变量声明：

```fr
let answer = 42;
```

导入语句：

```fr
import "helper.fr";
```

输出语句：

```fr
print("hello");
```

表达式语句：

```fr
answer;
```

代码块：

```fr
{
  let x = 1;
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

break 语句：

```fr
while true {
  break;
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

`else` 可以省略：

```fr
if true {
  print("visible");
}
```

函数声明：

```fr
fn add(a, b) {
  return a + b;
}
```

return 语句：

```fr
return 123;
```

future 块：

```fr
future {
  return 42;
}
```

## `print` 语法

第一版把 `print` 当作特殊语句，而不是普通函数调用。

固定格式：

```fr
print(表达式);
```

这里的外层括号是 `print` 语法的一部分，不会生成 `GroupingExpr`。

例如：

```fr
print(1 + 2);
```

会解析成：

```txt
PrintStmt(
  BinaryExpr(1, "+", 2)
)
```

普通表达式里的括号才会生成 `GroupingExpr`。

例如：

```fr
print((1 + 2) * 3);
```

会解析成：

```txt
PrintStmt(
  BinaryExpr(
    GroupingExpr(BinaryExpr(1, "+", 2)),
    "*",
    3
  )
)
```

## 当前支持的表达式

字面量：

```fr
123
12.5
"hello"
true
false
nil
```

变量读取：

```fr
answer
```

List 字面量：

```fr
[1, 2, 3]
```

Map 字面量：

```fr
{"name": "FR", "version": 1}
```

索引读取：

```fr
items[0]
user["name"]
```

括号表达式：

```fr
(1 + 2)
```

一元表达式：

```fr
!true
-1
```

二元表达式：

```fr
1 + 2
3 * 4
answer == 42
ready and count > 0
name == "FR" or name == "fr"
```

赋值表达式：

```fr
answer = answer + 1
```

索引赋值：

```fr
items[1] = 42
user["version"] = 2
```

函数调用：

```fr
add(1, 2)
```

await 表达式：

```fr
await future {
  return 42;
}
```

## 表达式优先级

当前优先级从低到高：

```txt
=
or
and
== !=
> >= < <=
+ -
* /
await ! -
字面量 / 变量 / 括号
函数调用
```

示例：

```fr
print(1 + 2 * 3);
```

会解析成：

```txt
1 + (2 * 3)
```

## 当前 AST 节点

表达式节点：

- `LiteralExpr`
- `VariableExpr`
- `ListExpr`
- `MapExpr`
- `IndexExpr`
- `AssignExpr`
- `IndexAssignExpr`
- `GroupingExpr`
- `UnaryExpr`
- `AwaitExpr`
- `FutureExpr`
- `BinaryExpr`
- `CallExpr`

语句节点：

- `VarStmt`
- `ImportStmt`
- `PrintStmt`
- `ExprStmt`
- `BlockStmt`
- `WhileStmt`
- `BreakStmt`
- `IfStmt`
- `FunctionStmt`
- `ReturnStmt`

程序节点：

- `Program`

## 暂未支持

后续会继续扩展真正的任务队列、异步调度器和更完整的模块语义。
