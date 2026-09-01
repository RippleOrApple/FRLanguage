# 自主开发任务计划

## 目标

持续推进 FRLanguage 的自举路线：先把 FR Lexer demo 演进为可复用工具链组件，再用 FR 实现 Parser 子集和解释器子集，最终形成可验证的最小自举闭环。

## 阶段

- [x] 阶段 0：确认仓库状态、近期路线和现有解释器结构。
- [x] 阶段 1：用测试先定义内置函数行为。
- [x] 阶段 2：实现原生函数调用模型和字符串/集合内置函数。
- [x] 阶段 3：实现受限 `readFile` 并接入 CLI 源码目录。
- [x] 阶段 4：补充示例和文档。
- [x] 阶段 5：运行完整验证并记录结果。
- [x] 阶段 6：增加 `and` / `or` 短路逻辑运算。
- [x] 阶段 7：增加 `break` 跳出循环能力。
- [x] 阶段 8：用新语法清理 FR Lexer demo，更新文档并验证。
- [x] 阶段 9：实现最小 `import "文件.fr";` 模块导入。
- [x] 阶段 10：拆分 FR Lexer demo helper，更新文档并验证。
- [x] 阶段 11：给核心源码补充学习型函数说明。
- [x] 阶段 12：给 import 失败补充导入上下文。
- [x] 阶段 13：增加字符判断内置函数，简化 FR Lexer demo。
- [x] 阶段 14：扩展 FR Lexer demo，支持关键字、字符串、注释、空白和更多符号。
- [x] 阶段 15：让 FR Lexer demo 输出 literal、行列号和错误 Token。
- [x] 阶段 16：增加 Python Lexer 与 FR Lexer 的结构化对照测试。
- [x] 阶段 17：增加 FR Lexer 错误 Token 与 Python Lexer 错误信息的对照测试。
- [x] 阶段 18：增加字符串转义支持，并让 Python Lexer、解释器和 FR Lexer demo 行为对齐。
- [x] 阶段 19：增加显式 `nil` 字面量，并同步 Python 语言链路和 FR Lexer demo。
- [x] 阶段 20：用 FR 实现简化 Parser，先支持 `let`、`print` 和基础表达式 AST。
- [x] 阶段 21：让 FR Parser 子集与 Python Parser 在小型样例上做结构化对照。
- [x] 阶段 22：用 FR 实现解释器子集，先运行字面量、变量、二元表达式和 `print`。
- [x] 阶段 23：打通最小自举闭环：Python FR 解释器运行 FR 工具链，FR 工具链运行小型 FR 程序。
- [ ] 阶段 24：逐步扩展 FR Parser/Interpreter，覆盖 `if`、`while`、函数和 Future。

## 决策

- 内置函数作为全局变量注入解释器，不新增语法。
- `readFile` 只接受相对路径，并限制在解释器 `base_path` 目录内。
- 保留当前树遍历解释器结构，不拆大模块。
- 自举先以结构化 Map/List 表达 Token 和 AST，不急着在 FR 里实现类或 dataclass。
- FR Parser 第一版只覆盖最小子集，后续通过对照测试逐步扩展。

## 风险

- 内置函数错误信息需要保持和现有运行时错误风格一致。
- 文件读取测试要避免依赖本机绝对路径。
- 自举目标很大，必须保持小步可验证；每一阶段都要能单独运行和测试。
- FR 目前没有异常机制，FR 写的工具链先用 `ERROR` Map 或错误列表表达诊断。
