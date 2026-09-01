# 长期项目规划

本文档记录 FRLanguage 的长期路线。它不是必须严格执行的排期，而是一张学习型路线图：每个阶段都应该有清楚目标、可验证产出和明确停止点。

当前项目已经完成一条最小语言链路：

```txt
源码 -> Lexer -> Parser -> AST -> Interpreter -> Runtime -> 输出
```

后续规划分为三个层次：

- 近期：让当前解释器更稳定、更好用。
- 中期：补齐写复杂程序需要的语言能力。
- 长期：探索字节码、自举和用 FR 写 FR 工具链。

## 阶段 1：项目收口和工程体验

目标：让当前项目成为一个稳定、可运行、可学习的小语言工具。

重点任务：

- 清理类型注解，减少编辑器类型检查红线。
- 增加更多错误场景测试。
- 统一错误信息格式。
- 完善 README 和示例程序。
- 增加命令行入口的边界测试。

建议新增测试：

```fr
print(1 / 0);
print(missing);
print(await 1);
add(1);
```

阶段产出：

- 命令行错误信息稳定。
- 常见错误都有测试覆盖。
- README 能让新读者独立运行项目。

完成标准：

- 全量测试通过。
- 示例程序都能运行。
- 主要错误不再直接暴露 Python traceback。

## 阶段 2：基础数据结构

目标：让 FR 能写更复杂的程序，为未来自举做准备。

当前已完成：

- List 列表
- Map 字典
- 索引读取
- 索引赋值
- `nil` 空值字面量
- 逻辑运算符 `and` / `or`
- `break` 跳出循环

已经继续完成：

- 字符串内置函数
- 文件 IO

示例语法：

```fr
let items = [1, 2, 3];
print(items[0]);

let user = {"name": "fr"};
print(user["name"]);
```

需要改动：

- Lexer：补 `[`、`]`、`:` 等符号。
- Parser：补集合字面量和索引表达式。
- AST：新增 `ListExpr`、`MapExpr`、`IndexExpr`。
- Interpreter：实现列表、字典和索引逻辑。

阶段产出：

- 能用 FR 表达 Token 列表、AST 列表、配置表。
- 能写简单的数据处理程序。

完成标准：

- List 和 Map 有完整行为测试。
- 错误边界清楚，例如索引越界、非法 key。

## 阶段 3：字符串和内置函数

目标：让 FR 能处理源码文本和基础数据转换。

当前已完成：

- `len(value)`
- `str(value)`
- `number(value)`
- `type(value)`
- `hasKey(map, key)`
- `substring(text, start, end)`
- `charAt(text, index)`
- `isDigit(ch)`
- `isAlpha(ch)`
- `isAlphaNumeric(ch)`
- `codePoint(ch)`
- `push(list, value)`
- `pop(list)`
- 字符串转义：`\"`、`\\`、`\n`、`\t`、`\r`

示例：

```fr
let text = "hello";
print(len(text));
print(charAt(text, 1));
print(isAlphaNumeric("_"));
print(codePoint("A"));
```

阶段产出：

- FR 能处理字符串扫描。
- FR 能实现简单 Lexer demo。
- Python Lexer 和 FR Lexer demo 能在转义字符串样例上保持一致。

完成标准：

- 字符串和 List 的常用操作都能用。
- 内置函数参数错误有清楚提示。
- FR Lexer demo 可以直接复用字符判断函数，不必在示例里手写数字判断。

## 阶段 4：文件 IO 和模块系统

目标：让 FR 程序能读取源码文件，并把大程序拆成多个文件。

当前已完成最小文件能力：

```fr
let source = readFile("hello.fr");
print(source);
```

当前已完成最小模块导入：

```fr
import "lexer.fr";
```

后续再扩展完整模块系统。

需要注意：

- 文件路径应限制在项目可控范围内。
- 模块导入需要避免重复执行。
- 错误信息要显示导入上下文。

阶段产出：

- FR 能读取 `.fr` 源码。
- FR 项目可以拆分文件。

完成标准：

- `readFile` 有测试。
- `import` 有重复导入和路径错误测试。
- 导入文件出错时能看到是哪个导入触发的。

## 阶段 5：更完整的 Future 和 Runtime

目标：让 Future 更接近真正异步模型。

当前 Future 已经支持：

```txt
创建 Future -> 入队 -> await 时运行任务 -> resolve/reject
```

后续可以继续做：

- pending Future
- await 暂停当前任务
- Future 完成后恢复任务
- 多个 Future 的调度顺序
- Future 错误传播链

示例目标：

```fr
let a = future {
  return 1;
};

let b = future {
  return 2;
};

print(await a + await b);
```

阶段产出：

- Runtime 不只是 `await` 时临时跑队列。
- Future 有更清楚的生命周期。

完成标准：

- 可以表达多个 Future 的调度顺序。
- Future 失败不会破坏整个 Runtime 状态。

## 阶段 6：REPL 交互式命令行

目标：让 FR 更适合学习和调试。

交互形式：

```txt
fr> let x = 1;
fr> print(x);
1
```

需要解决：

- 多行输入。
- 保留全局环境。
- 错误后继续运行。
- 显示表达式结果。

阶段产出：

- 可以通过 REPL 试语法。
- 学习语言时不用每次新建文件。

完成标准：

- REPL 有基础测试或脚本验证。
- 常见错误不会终止整个 REPL。

## 阶段 7：字节码虚拟机

目标：从树遍历解释器升级到更接近编译器的结构。

当前结构：

```txt
AST -> Interpreter 直接执行
```

目标结构：

```txt
AST -> Bytecode -> VM 执行
```

示例字节码：

```txt
CONST 1
CONST 2
ADD
STORE x
LOAD x
PRINT
```

需要新增模块：

- `compiler.py`
- `chunk.py`
- `opcode.py`
- `vm.py`

阶段产出：

- 同一份源码可以走解释器或 VM。
- 更清楚地区分 Parser、Compiler、Runtime。

完成标准：

- 基础表达式、变量、函数有 VM 测试。
- 解释器和 VM 的行为一致。

## 阶段 8：用 FR 写工具链的一部分

目标：开始自举探索，但不一口吃掉整个解释器。

推荐顺序：

1. 用 FR 写字符串扫描 demo。
2. 用 FR 写简化版 Lexer。
3. 用 FR 写简单表达式 Parser。
4. 用 FR 写解释器子集。
5. 用端到端测试验证最小自举闭环。

第一目标：

```txt
fr_lexer.fr
```

输入源码字符串，输出 Token 列表。

前置条件：

- List
- Map
- 字符串操作
- 文件 IO
- `and` / `or`
- `break`
- 模块系统

阶段产出：

- FR 能实现自己工具链中的一小块。
- 项目进入自举准备阶段。
- 第一条最小自举闭环可以运行变量、基础表达式、`print`、List/Map 字面量、索引读写、`if`、`while`、函数、递归和 `return`。

完成标准：

- `fr_lexer.fr` 能扫描一小部分 FR 源码。
- Python Lexer 和 FR Lexer 在测试样例上结果一致。
- FR Parser 子集能输出结构化 AST Map，并和 Python Parser 子集对齐。
- FR 解释器子集能运行小型 FR 程序，输出和 Python 实现一致。
- FR Parser/Interpreter 子集应逐步扩展，当前已覆盖集合字面量、索引读写、逻辑短路、控制流、函数、block 局部作用域、闭包读取和跨函数全局调用，下一步重点是评估 Future 是否进入自举子集。
- 对照测试应逐步覆盖基础源码、关键字、集合字面量、运算符和错误场景。
- 在 FR 没有异常机制前，词法错误可以先用 `ERROR` Token 表达。

## 阶段 9：自举解释器

目标：用 FR 写一个能运行小型 FR 程序的解释器。

目标形态：

```txt
Python 写的 FR 解释器
  运行
FR 写的 FR 解释器
  解释
FR 程序
```

建议范围：

- 先支持变量、表达式、print。
- 再支持 if、while、函数。
- 最后支持 Future。

阶段产出：

- `fr_interpreter.fr`
- 自举示例程序
- 对比测试
- 当前已有 `fr_interpreter_helpers.fr` 作为解释器子集雏形。

完成标准：

- FR 解释器能运行一组小型 FR 程序。
- Python 实现和 FR 实现的输出一致。

## 阶段 10：自举编译器

目标：让 FR 写的工具链生成字节码或中间表示。

目标形态：

```txt
FR 源码
 -> FR 写的编译器
 -> 字节码
 -> Python VM 或 FR VM 执行
```

这是长期探索阶段，不建议过早开始。

前置条件：

- 字节码 VM 稳定。
- FR 具备足够数据结构。
- FR 能读取文件和组织模块。
- FR Lexer/Parser 已经可用。

阶段产出：

- `fr_compiler.fr`
- 字节码输出格式
- 编译器自测程序

完成标准：

- FR 编译器能编译一个小型 FR 程序。
- 编译后的字节码能在 VM 中运行。

## 推荐执行顺序

近期最推荐：

```txt
阶段 1 收口 -> 模块系统 -> REPL
```

原因是这些阶段直接提升当前语言可用性，也为自举准备必要能力。

中期推荐：

```txt
阶段 5 -> 阶段 6 -> 阶段 7
```

这会让 Runtime、开发体验和编译器结构更清楚。

长期推荐：

```txt
阶段 8 -> 阶段 9 -> 阶段 10
```

这才是自举路线。不要在数据结构和 IO 不够时提前开始，否则会把大量精力耗在语言能力不足带来的绕路上。

## 当前最适合做的下一步

建议下一步做：

```txt
自举 Future 评估或运行时错误诊断
```

原因：

- FR Lexer、Parser 子集和 Interpreter 子集已经打通最小自举闭环。
- 当前自解释器已经具备环境链和函数闭包读取，下一块会开始触及 Future 或更严肃的错误传播。
- 这两者都会影响后续能否把更多工具链逻辑搬到 FR 里。
