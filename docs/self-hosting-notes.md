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
- `push`：向 Token 列表追加元素。
- `readFile`：读取源码文本。
- `import`：把工具函数拆到单独 `.fr` 文件。
- 导入错误上下文：导入失败时能看到是哪个文件触发的。
- `and` / `or`：组合扫描条件，并支持短路求值。
- `break`：在扫描循环中遇到边界字符时退出。

这些能力还不足以写完整编译器，但已经足够写一个非常小的扫描器。

## 当前 demo

示例文件：

```txt
examples/fr_lexer_demo.fr
examples/fr_lexer_helpers.fr
examples/fr_lexer_sample.fr.txt
```

它读取并扫描这段源码：

```fr
// demo comment
let name = "FR";
if name == "FR" {
  print(name);
}
```

输出的 Token 列表会包含关键字、标识符、字符串、比较运算符、括号和 EOF，例如：

```txt
[{"type": "LET", "lexeme": "let"}, {"type": "IDENT", "lexeme": "name"}, ... {"type": "EOF", "lexeme": ""}]
```

## 这个 demo 的限制

- 只输出 `type` 和 `lexeme`，还没有记录 literal、行号和列号。
- 字符串扫描还没有错误处理，遇到未闭合字符串时不会给出清楚错误。
- 未识别字符现在会被跳过，还没有错误 Token 或诊断信息。
- 模块系统还没有命名空间和导出控制。

## 下一步建议

优先补：

- 模块命名空间和导出控制：避免导入文件里的名字全部进入当前环境。
- 更完整的 FR Lexer：补 literal、行列号和未识别字符错误。

这些能力完成后，可以把 `fr_lexer_demo.fr` 扩展成真正的 `fr_lexer.fr`。
