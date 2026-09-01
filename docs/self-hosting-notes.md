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
examples/fr_lexer_helpers.fr
examples/fr_parser_helpers.fr
examples/fr_interpreter_helpers.fr
examples/fr_self_host_demo.fr
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

当前也已经有第一条最小自举闭环：

```txt
Python 写的 FR 解释器
  -> 运行 FR 写的 Lexer / Parser 子集 / Interpreter 子集
  -> 处理 examples/fr_parser_basic_sample.fr.txt
  -> 输出和 Python 原生链路一致
```

这个闭环暂时覆盖变量声明、`print`、字面量、变量读取、括号、一元表达式、基础二元表达式、`and/or` 短路逻辑、List/Map 字面量、索引读取、变量赋值、索引赋值、`if`、`while`、`break`、block 局部作用域、函数声明、函数调用、闭包读取、跨函数全局调用、递归和 `return`。

## 这个 demo 的限制

- 还没有覆盖 Python Lexer 的全部错误场景和恢复策略。
- 字符串扫描已经支持少量常用转义，但还没有 Unicode 转义、十六进制转义等扩展形式。
- 错误处理先用 `ERROR` Token 表达，还没有停止扫描或汇总诊断。
- FR Parser 子集还没有覆盖 `future` 和 `await`。
- FR 解释器子集还没有覆盖 Future、完整原生函数桥接和运行时错误诊断。
- 模块系统还没有命名空间和导出控制。

## 下一步建议

优先补：

- 模块命名空间和导出控制：避免导入文件里的名字全部进入当前环境。
- 评估 Future 是否进入自举子集：先判断它对 FR 工具链自举是否必要。
- 扩展 FR 解释器子集：补更完整的运行时错误、内置函数调用桥接和 Future。
- 更完整的 FR Lexer：继续补齐错误场景、错误汇总或更多字面量形式。

这些能力完成后，可以把当前 helper 文件整理成更正式的 FR 工具链目录。
