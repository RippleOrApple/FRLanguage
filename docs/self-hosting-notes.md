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
```

它扫描这段源码：

```fr
let answer = 42;
```

输出 Token 列表：

```txt
[{"type": "IDENT", "lexeme": "let"}, {"type": "IDENT", "lexeme": "answer"}, {"type": "EQUAL", "lexeme": "="}, {"type": "NUMBER", "lexeme": "42"}, {"type": "SEMICOLON", "lexeme": ";"}, {"type": "EOF", "lexeme": ""}]
```

## 这个 demo 的限制

- 只处理空格，不处理换行和注释。
- 标识符、关键字和数字扫描都很粗糙。
- 模块系统还没有命名空间和导出控制。

## 下一步建议

优先补：

- 模块命名空间和导出控制：避免导入文件里的名字全部进入当前环境。
- 更完整的 FR Lexer：让 demo 识别关键字、换行、注释和更多运算符。

这些能力完成后，可以把 `fr_lexer_demo.fr` 扩展成真正的 `fr_lexer.fr`。
