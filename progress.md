# 进度记录

## 2026-08-27

- 创建自主开发目标和计划文件。
- 确认当前分支为 `codex/list-support`，工作区干净。
- 确认 PR #2 已包含 List 和 Map 能力，下一步适合做字符串内置函数和最小文件 IO。
- 为 `len`、`charAt`、`substring`、`type`、`str`、`number`、`push`、`pop`、`readFile` 写了解释器测试。
- 运行 `$env:PYTHONPATH='src'; python -m unittest tests.test_interpreter`，新增测试按预期失败：内置函数未定义，`Interpreter` 尚不支持 `base_path`。
- 实现 `FRNativeFunction`，把内置函数注入解释器全局环境。
- 实现字符串、类型转换、List 修改和受限 `readFile`。
- 为 CLI 增加测试，确认 `readFile` 从源码文件所在目录解析相对路径；测试先按预期失败，再修改 `main.py` 传入 `source_path.parent`。
- 运行 `$env:PYTHONPATH='src'; python -m unittest tests.test_interpreter`，35 个解释器测试通过。
- 运行 `$env:PYTHONPATH='src'; python -m unittest tests.test_main`，4 个 CLI 测试通过。
- 新增 `examples/builtins.fr` 和 `examples/sample.txt`，展示字符串、List、Map、转换和 `readFile`。
- 新增 `examples/fr_lexer_demo.fr`，用 FR 自身扫描 `let answer = 42;` 并输出 Token 列表。
- 新增 `docs/self-hosting-notes.md`，记录自举准备能力、demo 限制和下一步建议。
- 运行 `$env:PYTHONPATH='src'; python -m frlang.main examples/builtins.fr`，示例输出符合预期。
- 运行 `$env:PYTHONPATH='src'; python -m frlang.main examples/fr_lexer_demo.fr`，示例输出 Token 列表。
- 提交前验证：
  - `$env:PYTHONPATH='src'; python -m unittest discover -s tests`：57 个测试通过。
  - `python -m compileall src tests`：通过。
  - `$env:PYTHONPATH='src'; python -m frlang.main examples/builtins.fr`：通过。
  - `$env:PYTHONPATH='src'; python -m frlang.main examples/fr_lexer_demo.fr`：通过。
