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
- 自举不应从完整编译器开始；当前最短路径是先用 FR 产出结构化 Token 和 AST，再写能执行 AST Map 的解释器子集。
- FR 当前没有异常机制，FR Parser 第一版可以用 `errors` 列表或 `ERROR` Map 表达诊断，先把正确路径跑通。
- FR Parser 子集用 Map 表达 AST 比追求类系统更贴合当前语言能力，测试也能直接把 Map 转回 Python dict 对照。
- 最小自举闭环已经可以先覆盖变量、基础表达式和 `print`；后续扩展的优先级应由自举工具链实际需要驱动。
- 集合能力是自举工具链的高优先级前置条件；FR Parser/Interpreter 子集支持 List/Map、索引和赋值后，就能承载更真实的 AST 和环境结构。
- 阶段 24 不能一次性标记完成；当前只完成 24.1，控制流、函数和 Future 仍需后续小步扩展。
- 控制流子集可以先复用单一环境执行 block；这和 Python 解释器的 block 局部作用域不同，但当前样例只需要外层变量更新，后续做函数/作用域时再补齐。
- `if/while` 加入后，自举样例已经能表达重复扫描和条件分支，下一块最有价值的是函数声明与调用。
- 自举函数调用先采用参数局部环境模型，足够支持普通函数和自身递归；还不支持闭包或函数体读取任意全局变量。
- `return` 可以用 Map 信号在 FR 自解释器内部传播，这延续了 Python 解释器里 `ReturnSignal` 的思路，但避免了新增宿主异常机制。
- FR 的 Map 缺少安全 membership 检查时，自解释器无法沿环境链查找变量，因为直接索引不存在的 key 会触发运行时错误。
- `hasKey(map, key)` 能复用现有 MapKey 规范化规则，既服务普通 FR 程序，也让 FR 自解释器可以实现 `values + enclosing` 的环境链。
- 自解释器函数声明记录 `closure` 后，递归、跨函数调用和读取声明位置外层变量都能依赖同一套查找逻辑。
- 自举 Parser 中 `or` 应位于赋值之下、`and` 之上，和 Python Parser 的逻辑优先级保持一致。
- 自举解释器执行 `and/or` 时不能预先计算右侧，否则会破坏短路规则，也会让副作用样例输出和 Python 实现不一致。
- `break` 在 FR 自解释器里可以表达成 `{"type": "BreakSignal"}`，block 和 if 只负责传递，while 负责消费。
- 函数调用边界暂时不会完整复刻 Python 对非法 break 的运行时错误；在自举错误模型补齐前，重点先覆盖 while 内合法 break。
- 自举 Future 不必一开始复刻 Python Runtime 队列；用 Map 保存 `pending/resolved`、body、closure 和 value，可以先验证延迟执行、await 触发和结果缓存。
- Future body 记录声明时环境后，可以覆盖“函数返回 Future，await 时仍能读取函数局部参数”的关键闭包场景。
- 目标程序调用 `len`、`push`、`str` 等内置函数时，自解释器不能直接拿宿主全局函数对象；用 `SelfNativeFunction` Map 作为占位，再由 FR helper 分派到宿主内置函数，能保持自举解释器自己的环境模型。
- 常用内置函数桥接后，自解释器运行目标程序时可以覆盖字符串处理、集合修改、Map membership、类型查询、转换和文件读取这批自举工具链高频能力。
- `runSelfHostedSourceResult` 比只返回输出的 `runSelfHostedSource` 更适合后续测试错误路径；正常 demo 仍可继续使用输出列表，避免打扰已有学习示例。
- 在 FR 还没有异常机制前，自举运行时错误先进入 `state["errors"]` 列表；这能先解决可观察性，后续再补“错误后是否停止执行”的语义。
- 把 FR 工具链核心文件放入 `examples/toolchain/` 后，测试可以直接导入正式组件；旧 helper 路径只作为兼容入口继续存在。
- 由于当前 `import` 禁止从子目录逃逸到父目录，兼容入口应放在 `examples/` 根目录向下导入 `toolchain/`，而不是在 `toolchain/` 内向上导入旧 helper。
- 自举解释器可以用 `reportUnhandledSelfSignal` 统一处理跑出合法边界的控制流信号：程序入口负责顶层 `return/break`，函数和 Future 边界负责未被 while 消费的 `break`。
- 当前错误策略仍是“记录后继续/返回 nil”，尚未完全复刻 Python 解释器遇到运行时错误即停止执行的行为。
- FR Parser 子集支持 `ImportStmt` 后，目标程序就能拆成多个文件；这比只在宿主测试脚本中 import 工具链更接近真实自举项目形态。
- 自举解释器的 import 缓存使用路径字符串即可覆盖当前 examples 下的重复导入样例；嵌套目录相对路径解析仍受限于宿主 `readFile` 的 base_path 模型。

## 路线判断

- `docs/roadmap.md` 当前推荐下一步是字符串内置函数。
- 文件 IO 是后续自举路线的前置能力，但本阶段只做 `readFile`，不做 `import`。

## 约束

- 文档写中文。
- 测试和代码不写入个人机器绝对路径。
