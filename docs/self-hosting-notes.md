# 自举准备笔记

本文档记录“未来用 FR 写 FR 工具链”之前需要具备的能力，以及当前已经能做的小 demo。

## 当前进展

FR 现在已经具备一批写 Lexer demo 需要的基础能力：

- List：保存 Token 序列。
- Map：表达 Token 对象，例如 `{"type": "NUMBER", "lexeme": "42"}`。
- `len`：读取字符串和集合长度。
- `charAt`：逐字符扫描源码。
- `substring`：截取词素。
- `push`：向 Token 列表追加元素。
- `readFile`：读取源码文本。
- `import`：把工具函数拆到单独 `.fr` 文件。
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

- 字符串判断函数：例如 `isDigit`、`isAlpha` 可以先作为 FR 函数练习，也可以以后做成内置函数。
- 导入链错误信息：导入失败时显示是哪个文件触发的。

这些能力完成后，可以把 `fr_lexer_demo.fr` 扩展成真正的 `fr_lexer.fr`。
