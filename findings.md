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

## 路线判断

- `docs/roadmap.md` 当前推荐下一步是字符串内置函数。
- 文件 IO 是后续自举路线的前置能力，但本阶段只做 `readFile`，不做 `import`。

## 约束

- 文档写中文。
- 测试和代码不写入个人机器绝对路径。
