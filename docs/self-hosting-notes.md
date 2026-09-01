# 自举准备笔记

本文档记录“未来用 FR 写 FR 工具链”之前需要具备的能力，以及当前已经能做的小 demo。

## 当前进展

FR 现在已经具备一批写 Lexer demo 需要的基础能力：

- List：保存 Token 序列。
- Map：表达 Token 对象，例如 `{"type": "NUMBER", "lexeme": "42"}`。
- `len`：读取字符串和集合长度。
- `charAt`：逐字符扫描源码。
- `substring`：截取词素。
- `isDigit` / `isAlpha` / `isAlphaNumeric`：判断字符类别。
- `codePoint`：识别换行、制表符和双引号这类不方便直接写进字符串的字符。
- `hasKey`：安全判断 Map 是否包含某个 key，用来实现 FR 自解释器的环境链查找。
- `push`：向 Token 列表追加元素。
- `readFile`：读取源码文本。
- `import`：把工具函数拆到单独 `.fr` 文件。
- 导入错误上下文：导入失败时能看到是哪个文件触发的。
- `and` / `or`：组合扫描条件，并支持短路求值。
- `break`：在扫描循环中遇到边界字符时退出。
- 字符串转义：可以直接写 `\"`、`\\`、`\n`、`\t` 和 `\r`。
- `nil` 字面量：可以直接表达空 literal，不必再写 `let literal;` 这类占位声明。

这些能力还不足以写完整编译器，但已经足够写一个非常小的扫描器、Parser 子集和解释器子集。

## 当前 demo

示例文件：

```txt
examples/fr_lexer_demo.fr
examples/fr_lexer_error_demo.fr
examples/fr_self_host_demo.fr
examples/fr_bootstrap_suite.fr
examples/fr_bootstrap_acceptance.fr
examples/fr_toolchain_self_load_probe.fr
examples/fr_nested_bootstrap_acceptance.fr.txt
examples/toolchain/lexer.fr
examples/toolchain/parser.fr
examples/toolchain/interpreter.fr
examples/toolchain/bootstrap.fr
examples/fr_lexer_helpers.fr
examples/fr_parser_helpers.fr
examples/fr_interpreter_helpers.fr
examples/fr_lexer_bad_char_sample.fr.txt
examples/fr_lexer_error_sample.fr.txt
examples/fr_lexer_unterminated_string_sample.fr.txt
examples/fr_lexer_unknown_escape_sample.fr.txt
examples/fr_lexer_escaped_string_sample.fr.txt
examples/fr_lexer_nil_sample.fr.txt
examples/fr_lexer_compare_sample.fr.txt
examples/fr_lexer_keywords_sample.fr.txt
examples/fr_lexer_sample.fr.txt
examples/fr_parser_basic_sample.fr.txt
examples/fr_parser_collections_sample.fr.txt
examples/fr_parser_control_flow_sample.fr.txt
examples/fr_parser_function_sample.fr.txt
examples/fr_parser_scope_sample.fr.txt
examples/fr_parser_logic_sample.fr.txt
examples/fr_parser_break_sample.fr.txt
examples/fr_parser_future_sample.fr.txt
examples/fr_parser_builtins_sample.fr.txt
examples/fr_parser_import_sample.fr.txt
examples/fr_parser_import_helper_sample.fr.txt
examples/fr_parser_error_sample.fr.txt
examples/fr_parser_top_level_return_error_sample.fr.txt
examples/fr_parser_top_level_break_error_sample.fr.txt
examples/fr_parser_function_break_error_sample.fr.txt
examples/fr_parser_future_break_error_sample.fr.txt
```

它读取并扫描这段源码：

```fr
// demo comment
let name = "FR";
if name == "FR" {
  print(name);
}
```

输出的 Token 列表会包含关键字、标识符、字符串、比较运算符、括号、literal、行列号和 EOF，例如：

```txt
[{"type": "LET", "lexeme": "let", "literal": nil, "line": 2, "column": 1}, ...]
```

错误样例会输出 `ERROR` Token，用来展示未识别字符和未闭合字符串的处理方式。当前 FR 还没有异常机制，所以 FR Lexer 不抛出错误，而是把错误作为 Token 放进扫描结果。

当前测试已经会把 FR Lexer 的输出和 Python Lexer 的输出做结构化对照，覆盖基础源码、更多符号、关键字样例、`nil` 样例、转义字符串样例和基础错误样例。

当前也已经有一条可验证的最小自举闭环：

```txt
Python 写的 FR 解释器
  -> 运行 FR 写的 Lexer / Parser 子集 / Interpreter 子集
  -> 处理多组 examples/fr_parser_*.fr.txt 目标程序
  -> 由 examples/toolchain/bootstrap.fr 对照 expected 输出和错误
```

这个闭环暂时覆盖变量声明、`print`、目标程序 `import`、字面量、变量读取、括号、一元表达式、基础二元表达式、`and/or` 短路逻辑、List/Map 字面量、索引读取、变量赋值、索引赋值、`if`、`while`、`break`、block 局部作用域、函数声明、函数调用、常用内置函数桥接、闭包读取、跨函数全局调用、递归、`return`、最小 `future/await`、基础运行时错误诊断和非法控制流诊断。

`examples/fr_bootstrap_acceptance.fr` 会调用 `runDefaultBootstrapExpectations()`，默认运行 15 个自举验收用例，并返回：

- `passed`：整体验收是否通过。
- `case_count`：验收用例数量。
- `passed_count`：通过数量。
- `failed_count`：失败数量。
- `cases`：每个目标程序的实际输出、实际错误和期望值。

目前还可以做一层更深的验证：

```txt
Python 写的 FR 解释器
  -> 运行 FR 写的自解释器
  -> 执行 examples/fr_nested_bootstrap_acceptance.fr.txt
  -> 目标程序导入 examples/toolchain/bootstrap.fr
  -> 内层 FR bootstrap 跑默认 15 个验收用例
```

对应测试会检查输出为 `true`、`15`、`0`，表示内层默认验收全部通过。为了支撑这种深层树遍历调用，Python 解释器初始化时会把宿主递归上限提升到一个学习项目可接受的范围。

## 这个 demo 的限制

- 还没有覆盖 Python Lexer 的全部错误场景和恢复策略。
- 字符串扫描已经支持少量常用转义，但还没有 Unicode 转义、十六进制转义等扩展形式。
- 错误处理先用 `ERROR` Token 表达，还没有停止扫描或汇总诊断。
- 自举 Future 目前是最小 Map 模型，还没有复刻 Python Runtime 队列、reject 状态或 Future 错误传播链。
- FR 解释器子集还没有覆盖完整错误传播和停止执行策略。
- 自举 import 目前已经能按目标文件目录解析同级导入，例如 `toolchain/bootstrap.fr` 内部的 `import "lexer.fr";` 会解析到 `toolchain/lexer.fr`；但仍没有路径归一化、命名空间和导出控制。
- 深层二级自举依然依赖 Python 宿主解释器的调用栈、内置函数桥接和 `readFile` 文件 IO，还不等于完全由 FR 独立运行。

## 下一步建议

优先补：

- 模块命名空间和导出控制：避免导入文件里的名字全部进入当前环境。
- 扩展 FR 解释器子集：补更完整的错误传播、Future 错误传播和非法控制流边界。
- 更完整的 FR Lexer：继续补齐错误场景、错误汇总或更多字面量形式。
- 长期优化执行模型：减少树遍历解释器对 Python 调用栈的依赖，为更深层自举或 VM 做准备。

当前 helper 文件已经整理成 `examples/toolchain/` 下的正式 FR 工具链组件；旧 helper 路径保留为兼容入口。
