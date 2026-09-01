# FRLanguage
一个抱着学习目的创建的语言

FRLanguage 是一个使用 Python 编写的教学型小语言项目。目标不是追求完整编译器，而是做出一个结构清晰、可运行、可逐步扩展的解释器，并加入类似 Dart 的 Future 特性。

当前已经具备一条完整链路：

```txt
源码 -> Token -> AST -> Interpreter -> Runtime -> 输出
```

## 文档

- [阶段开发规划](docs/stages.md)
- [长期项目规划](docs/roadmap.md)
- [项目结构说明](docs/project-structure.md)
- [语言设计草案](docs/language-draft.md)
- [词法分析器说明](docs/lexer.md)
- [语法分析器说明](docs/parser.md)
- [解释器说明](docs/interpreter.md)
- [Future 和 await 说明](docs/future.md)
- [自举准备笔记](docs/self-hosting-notes.md)

FR 写的工具链核心组件已经整理到 `examples/toolchain/`：

- `examples/toolchain/lexer.fr`
- `examples/toolchain/parser.fr`
- `examples/toolchain/interpreter.fr`

## 当前支持的语法

- 变量声明：`let x = 1;`
- 赋值：`x = x + 1;`
- 输出：`print(x);`
- 表达式：数字、字符串、布尔值、`nil`、变量、括号、一元运算、二元运算
- 字符串转义：`\"`、`\\`、`\n`、`\t`、`\r`
- List：`[1, 2, 3]`
- 索引读取和赋值：`items[0]`、`items[1] = 42`
- Map：`{"name": "FR"}`
- 内置函数：`len(value)`、`charAt(text, index)`、`substring(text, start, end)`、`isDigit(ch)`、`isAlpha(ch)`、`isAlphaNumeric(ch)`、`codePoint(ch)`
- 类型和转换：`type(value)`、`str(value)`、`number(value)`
- Map 辅助：`hasKey(map, key)`
- List 修改：`push(list, value)`、`pop(list)`
- 文件读取：`readFile("相对路径")`
- 模块导入：`import "相对路径.fr";`
- 逻辑运算：`and`、`or`
- 条件分支：`if 条件 { ... } else { ... }`
- 循环：`while 条件 { ... }`、`break;`
- 代码块作用域：`{ ... }`
- 函数：`fn add(a, b) { return a + b; }`
- 函数调用：`add(1, 2)`
- 递归函数
- Future：`future { return 42; }`
- await：`await future值`

## 运行示例

当前可以通过模块入口运行 `.fr` 文件：

```bash
$env:PYTHONPATH='src'; python -m frlang.main examples/hello.fr
```

更多示例：

```bash
$env:PYTHONPATH='src'; python -m frlang.main examples/while.fr
$env:PYTHONPATH='src'; python -m frlang.main examples/if.fr
$env:PYTHONPATH='src'; python -m frlang.main examples/list.fr
$env:PYTHONPATH='src'; python -m frlang.main examples/map.fr
$env:PYTHONPATH='src'; python -m frlang.main examples/builtins.fr
$env:PYTHONPATH='src'; python -m frlang.main examples/fr_lexer_demo.fr
$env:PYTHONPATH='src'; python -m frlang.main examples/fr_lexer_error_demo.fr
$env:PYTHONPATH='src'; python -m frlang.main examples/fr_self_host_demo.fr
$env:PYTHONPATH='src'; python -m frlang.main examples/function.fr
$env:PYTHONPATH='src'; python -m frlang.main examples/recursion.fr
$env:PYTHONPATH='src'; python -m frlang.main examples/future.fr
$env:PYTHONPATH='src'; python -m frlang.main examples/future_order.fr
```

## 运行测试

项目测试使用 Python 标准库 `unittest`，不需要额外安装 `pytest`。

```bash
$env:PYTHONPATH='src'; python -m unittest discover -s tests
```

## 错误处理

命令行入口会捕获语言错误，并输出简短中文错误信息。

例如：

```fr
print(missing);
```

会输出类似：

```txt
错误：第 1 行，第 7 列：变量 missing 未定义
```

## 当前限制

- 没有静态类型检查
- 模块系统还很小，只支持执行式 `import "文件.fr";`
- 没有类和对象系统
- Runtime 是协作式任务队列，不是真正多线程或 IO 异步
- `await` 当前通过 Runtime 队列运行 Future 任务，还没有完整的暂停和恢复调用栈模型
- 自举工具链目前只覆盖子集：FR Parser/Interpreter 子集可运行变量、基础表达式、`print`、List/Map 字面量、索引读写、`and/or` 短路逻辑、`if`、`while`、`break`、block 局部作用域、函数调用、常用内置函数桥接、闭包读取、跨函数全局调用、递归、`return`、最小 `future/await`、基础运行时错误诊断和非法控制流诊断

## 后续方向

- 扩展模块系统，例如命名空间、导出控制和更完整的导入链展示
- 清理类型注解，减少编辑器类型检查红线
- 增加更多错误测试
- 做 REPL 交互式命令行
- 扩展真正的异步恢复模型
