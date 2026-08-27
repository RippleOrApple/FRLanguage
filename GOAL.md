# Goal

## Objective

在用户散步期间，自主推进 FRLanguage 的近期路线，让语言更接近“能用 FR 写工具链小 demo”。

## Scope

- 增加字符串和集合相关内置函数。
- 增加最小文件读取能力。
- 增加测试、示例和中文文档。
- 保持当前解释器结构简洁，不引入大型依赖。

## Non-goals

- 不实现模块系统。
- 不实现真正异步 IO。
- 不重写 Parser、Interpreter 或 Runtime 架构。
- 不开始字节码 VM。

## Acceptance Criteria

- FR 程序可以调用内置函数处理字符串、List、Map。
- FR 程序可以通过受限的相对路径读取文本文件。
- 新行为有单元测试覆盖。
- README、docs 和 examples 记录新增能力。
- 全量测试、编译检查和新增示例运行通过。

## Constraints

- 文档使用中文。
- 代码中不写入个人机器的绝对路径。
- 改动尽量小，优先延续现有项目风格。

