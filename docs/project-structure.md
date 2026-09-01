# 项目结构说明

FRLanguage 使用解释器流水线划分项目结构：

```txt
源码 -> Token -> AST -> 解释执行 -> Future 运行时
```

目录结构：

```txt
FRLanguage/
├─ README.md
├─ docs/
│  ├─ stages.md
│  ├─ project-structure.md
│  └─ language-draft.md
├─ examples/
│  ├─ hello.fr
│  ├─ function.fr
│  ├─ fr_lexer_helpers.fr
│  ├─ fr_parser_helpers.fr
│  ├─ fr_interpreter_helpers.fr
│  ├─ fr_self_host_demo.fr
│  ├─ future.fr
│  └─ toolchain/
│     ├─ lexer.fr
│     ├─ parser.fr
│     └─ interpreter.fr
├─ src/
│  └─ frlang/
│     ├─ __init__.py
│     ├─ main.py
│     ├─ token.py
│     ├─ lexer.py
│     ├─ ast.py
│     ├─ parser.py
│     ├─ environment.py
│     ├─ interpreter.py
│     ├─ runtime.py
│     ├─ future.py
│     └─ errors.py
└─ tests/
   ├─ test_lexer.py
   ├─ test_parser.py
   ├─ test_interpreter.py
   └─ test_future.py
```

## `src/frlang/main.py`

命令行入口。

职责：

- 读取 `.fr` 源码文件
- 调用词法分析器
- 调用语法分析器
- 启动解释器
- 输出错误信息

## `src/frlang/token.py`

Token 定义。

职责：

- 定义 Token 类型
- 保存 Token 文本、字面量、行号、列号
- 为 Lexer 和 Parser 提供统一的数据结构

## `src/frlang/lexer.py`

词法分析器。

职责：

- 扫描源码字符串
- 识别关键字、标识符、数字、字符串、符号
- 生成 Token 列表
- 报告词法错误

## `src/frlang/ast.py`

AST 节点定义。

职责：

- 定义表达式节点
- 定义语句节点
- 作为 Parser 和 Interpreter 之间的数据结构边界

## `src/frlang/parser.py`

语法分析器。

职责：

- 把 Token 列表解析成 AST
- 处理表达式优先级
- 识别语句结构
- 报告语法错误

## `src/frlang/environment.py`

变量环境。

职责：

- 保存变量和值
- 支持嵌套作用域
- 处理变量定义、读取和赋值

## `src/frlang/interpreter.py`

解释器核心。

职责：

- 执行语句
- 计算表达式
- 调用函数
- 与运行时协作处理 `await`

## `src/frlang/future.py`

Future 对象。

职责：

- 保存 Future 状态
- 保存完成值或错误
- 注册完成回调
- 提供 resolve 和 reject 行为

## `src/frlang/runtime.py`

运行时和调度器。

职责：

- 管理任务队列
- 调度 Future
- 在 `await` 时驱动任务队列
- 作为异步能力的集中入口

## `src/frlang/errors.py`

错误类型。

职责：

- 定义词法错误
- 定义语法错误
- 定义运行时错误
- 统一错误格式

## `examples/`

语言示例。

职责：

- 展示语法
- 辅助手动测试
- 作为文档补充
- 保存 FR 写的工具链 demo 和自举样例

## `examples/toolchain/`

FR 写的工具链核心组件。

职责：

- `lexer.fr`：用 FR 扫描源码并生成结构化 Token List。
- `parser.fr`：用 FR 把 Token List 转成 AST Map。
- `interpreter.fr`：用 FR 执行 AST Map，并返回输出和基础错误诊断。
- 支撑 `fr_self_host_demo.fr` 和 `tests/test_examples.py` 中的端到端自举对照。

`examples/fr_lexer_helpers.fr`、`examples/fr_parser_helpers.fr` 和 `examples/fr_interpreter_helpers.fr` 目前保留为兼容入口，它们会导入 `toolchain/` 下的新文件。

## `tests/`

自动化测试。

职责：

- 测试词法分析器
- 测试语法分析器
- 测试解释器
- 测试 Future 行为
