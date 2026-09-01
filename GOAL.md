# Goal

## Objective

持续推进 FRLanguage 的自举路线，最终做到：由 Python 写的 FR 解释器运行 FR 写的工具链核心组件，再由这些 FR 组件处理并运行小型 FR 程序。

## Scope

- 把现有 FR Lexer demo 演进成可复用的 FR 工具链组件。
- 用 FR 逐步实现 Parser 子集，先输出 AST Map，再扩展语句和表达式覆盖范围。
- 用 FR 逐步实现解释器子集，先运行变量、表达式和 `print`，再扩展控制流、函数和 Future。
- 每个阶段都要有 Python 侧测试或示例对照，避免只靠手工观察输出。
- 继续维护中文文档、阶段计划、发现记录和进度记录。

## Non-goals

- 不追求一次性完整替换 Python 解释器。
- 不在自举链路稳定前实现大型标准库、类系统或复杂类型系统。
- 不为了自举提前引入大型第三方依赖。
- 不把当前树遍历解释器重写成 VM，除非后续阶段明确切换目标。

## Acceptance Criteria

- FR 写的 Lexer 能扫描自举样例所需源码，并和 Python Lexer 在测试样例上对齐。
- FR 写的 Parser 能把小型 FR 程序转换成结构化 AST Map。
- FR 写的解释器能执行由 FR Parser 产出的 AST Map，至少覆盖变量声明、表达式和 `print`。
- 存在端到端测试：Python FR 解释器运行 FR 工具链，FR 工具链再处理一个小型 FR 程序，输出和 Python 实现一致。
- 全量测试、编译检查和关键示例运行通过。

## Constraints

- 文档使用中文。
- 代码和测试不写入个人机器绝对路径。
- 每个新增函数都要有简短易懂的注释或文档字符串，说明用途和意义。
- 改动保持小步提交，优先延续当前项目结构和风格。

## Notes

- 当前最短自举路径是：FR Lexer -> FR Parser 子集 -> FR Interpreter 子集 -> 端到端对照测试。
- 真正完整自举会很长，阶段产出要保持可运行、可测试、可回退。
