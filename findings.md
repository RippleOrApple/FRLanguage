# 发现记录

## 代码结构

- `src/frlang/interpreter.py` 已经支持函数声明、函数调用、List、Map、Future。
- 调用表达式当前只接受 `FRFunction`，适合扩展出 `FRNativeFunction`。
- `src/frlang/main.py` 负责读取 `.fr` 文件并调用 `run_source`。
- 测试使用 `unittest`，解释器测试直接构造 `Lexer -> Parser -> Interpreter`。
- 原生函数可以复用现有调用表达式，只需要和用户函数提供同样的 `arity()` / `call()` 接口。
- `readFile` 应从 `main.py` 传入源码文件所在目录，否则命令行运行时会按当前工作目录查找文件。
- 当前 FR 还没有 `break`、`and`、`or`，所以 FR 版扫描器 demo 需要用布尔变量控制循环退出。
- `and/or` 需要短路求值，不能复用普通二元表达式里“先算左右两边”的流程。
- `break` 用内部控制流信号最贴合现有 `ReturnSignal` 模型，但需要禁止穿过函数边界。
- `break` 在 `future` 块中如果没有被 `while` 捕获，应作为 Future 失败错误传播，而不是泄漏内部控制流异常。
- 最小 `import` 可以先作为语句实现，不需要新增表达式能力。
- 导入文件应复用同一个解释器、全局环境、输出列表和导入缓存，这样 helper 文件定义的函数能被主文件使用。
- 现阶段 `import` 不做命名空间隔离，导入文件里的声明会进入执行时所在环境；顶层导入能自然暴露 helper 函数。
- 导入失败时应从 `imported_paths` 中移除该文件，避免失败文件被错误地视为已导入。
- 字符判断函数适合先做成原生函数，因为 FR Lexer demo 会频繁使用它们，而且能明显减少 helper 代码噪音。
- FR 早期没有字符串转义语法，所以扫描双引号和换行时曾需要借助 `codePoint(ch)` 这类字符编码函数。
- 当 FR Lexer demo 需要返回多个扫描状态时，Map 比多个并行变量更适合，后续可以自然演化成 scanner 对象。
- FR Lexer 和 Python Lexer 做结构化对照时，直接读取解释器里的运行时 List/Map 比解析打印文本更可靠。
- FR 当前没有异常机制，FR Lexer 用 `ERROR` Token 表达错误更贴合现阶段能力；测试可以只对齐核心错误消息。
- 字符串转义让 FR helper 可以直接写双引号、反斜杠、换行、制表符和回车，不再需要所有特殊字符都依赖 `codePoint` 辅助判断。
- 未知字符串转义应在消费反斜杠和后续字符后立刻报错；此时错误词素不包含尚未消费的闭合引号。
- 显式 `nil` 字面量让源码、Map literal 和 FR Lexer helper 都能直接表达空值，不必再依赖未初始化变量制造 None。

## 路线判断

- `docs/roadmap.md` 当前推荐下一步是字符串内置函数。
- 文件 IO 是后续自举路线的前置能力，但本阶段只做 `readFile`，不做 `import`。

## 约束

- 文档写中文。
- 测试和代码不写入个人机器绝对路径。
