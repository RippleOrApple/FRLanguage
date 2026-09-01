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
- [x] 阶段 24：逐步扩展 FR Parser/Interpreter，覆盖 `if`、`while`、函数和 Future。
  - [x] 阶段 24.1：扩展 FR Parser/Interpreter 子集，支持 List/Map 字面量、索引读取、变量赋值和索引赋值。
  - [x] 阶段 24.2：扩展 FR Parser/Interpreter 子集，支持 `if`、`while` 和 block。
  - [x] 阶段 24.3：扩展 FR Parser/Interpreter 子集，支持函数声明、函数调用、递归和 `return`。
  - [x] 阶段 24.4：扩展 FR 自解释器环境模型，支持 block 局部作用域、函数闭包读取和跨函数全局调用。
  - [x] 阶段 24.5：扩展 FR Parser/Interpreter 子集，支持 `and` / `or` 逻辑表达式和短路求值。
  - [x] 阶段 24.6：扩展 FR Parser/Interpreter 子集，支持 `break` 跳出 `while`。
  - [x] 阶段 24.7：实现最小自举 Future/await：Future 延迟执行、await 触发执行并缓存结果。
- [ ] 阶段 25：提升自举工具链质量，补运行时错误诊断、原生函数桥接边界和更正式的 FR 工具链组织。
  - [x] 阶段 25.1：让 FR 自解释器注册并调用常用内置函数，包括字符串、集合、类型转换、Map 辅助和文件读取。
  - [x] 阶段 25.2：补基础自举运行时错误诊断，让缺失变量、非法调用和非法 await 不再静默变成 nil 或宿主异常。
  - [x] 阶段 25.3：补非法控制流边界诊断，覆盖顶层 `return`、顶层 `break`、函数裸 `break` 和 Future 裸 `break`。
  - [x] 阶段 25.4：整理 FR 工具链文件组织，逐步从 demo helper 过渡到更正式的自举组件。
  - [x] 阶段 25.5：让 FR Parser/Interpreter 子集支持目标程序中的 `import`，并缓存重复导入。
  - [ ] 阶段 25.6：补更完整的错误传播和停止执行策略。
- [x] 阶段 26：建立更正式的自举验证入口和验收样例。
  - [x] 阶段 26.1：新增 FR 写的 `bootstrap.fr`，统一运行多组目标源码并返回结构化自举结果。
  - [x] 阶段 26.2：扩展 bootstrap suite，覆盖更多目标程序和错误路径，并由 FR 计算 expected 对照、通过数和失败数。
- [ ] 阶段 27：继续减少自举验证对 Python 测试脚手架的依赖，补更强的错误传播和更复杂目标程序。

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
- 自解释器环境链需要能判断 Map 中是否存在某个名字，因此 `hasKey(map, key)` 是自举作用域模型的低成本前置能力。
- 自举解释器里的 `and/or` 必须在计算右侧表达式前处理，否则带函数调用或赋值副作用的右侧会破坏短路语义。
- 自举解释器里的 `break` 可以复用 `return` 的 Map 信号传播方式，但应只由最近的 `while` 消费。
- 自举 Future 第一版用 Map 表达 pending/resolved 状态，不做真正 Runtime 队列；这足够先验证语法、闭包和 await 缓存语义。
- 自举内置函数桥接先注册 `SelfNativeFunction` 占位对象，再在调用时转发到宿主 FR 内置函数，避免目标程序只能调用用户自定义函数。
- 自举运行时错误先进入 `errors` 列表，不立刻中断程序；后续再决定是否补类似异常的控制流。
- FR 工具链核心文件已移动到 `examples/toolchain/`；旧 helper 文件保留为兼容入口，降低示例和学习材料迁移成本。
- 未被合法边界消费的 `ReturnSignal` / `BreakSignal` 应在程序入口、函数调用或 Future 执行边界转成错误诊断。
- 自举 `import` 先用路径字符串做缓存 key，路径安全和文件读取仍交给宿主 `readFile` 负责。
- `bootstrap.fr` 是比打印 demo 更正式的验证入口，适合后续逐步承载自举验收用例。
- 默认 bootstrap 验收集合先覆盖 15 个目标程序，包含正常输出路径和错误诊断路径，并由 FR 代码自己计算 `passed_count` / `failed_count`。
