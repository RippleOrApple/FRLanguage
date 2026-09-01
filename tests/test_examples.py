import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

from frlang.ast import (
    AssignExpr,
    AwaitExpr,
    BinaryExpr,
    BreakStmt,
    BlockStmt,
    CallExpr,
    Expr,
    ExprStmt,
    FunctionStmt,
    FutureExpr,
    GroupingExpr,
    IfStmt,
    IndexAssignExpr,
    IndexExpr,
    ListExpr,
    LiteralExpr,
    MapExpr,
    PrintStmt,
    Program,
    ReturnStmt,
    Stmt,
    UnaryExpr,
    VarStmt,
    VariableExpr,
    WhileStmt,
)
from frlang.errors import LexerError
from frlang.interpreter import Interpreter, MapKey
from frlang.lexer import Lexer
from frlang.main import main
from frlang.parser import Parser


class ExampleTest(unittest.TestCase):
    """验证 examples 目录中的 FR 示例程序仍然可以作为学习材料运行。"""

    def run_example(self, path: str) -> str:
        """运行一个示例文件，并返回它打印到标准输出的文本。"""
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            main([path])
        return stdout.getvalue()

    def run_fr_lexer(self, source_path: str) -> list[dict[str, Any]]:
        """运行 FR 写的 Lexer，并把内部 Map/List 结果转换成 Python 值。"""
        program_source = f"""
        import "toolchain/lexer.fr";
        let actual = scan(readFile("{source_path}"));
        """
        tokens = Lexer(program_source).scan_tokens()
        program = Parser(tokens).parse()
        interpreter = Interpreter(base_path=Path("examples"))
        interpreter.interpret(program)
        return self.normalize_fr_value(interpreter.globals.values["actual"])

    def run_fr_parser(self, source_path: str) -> dict[str, Any]:
        """运行 FR 写的 Parser 子集，并返回转换后的 AST Map。"""
        program_source = f"""
        import "toolchain/lexer.fr";
        import "toolchain/parser.fr";
        let actual = parseSource(readFile("{source_path}"));
        """
        tokens = Lexer(program_source).scan_tokens()
        program = Parser(tokens).parse()
        interpreter = Interpreter(base_path=Path("examples"))
        interpreter.interpret(program)
        return self.normalize_fr_value(interpreter.globals.values["actual"])

    def run_fr_self_interpreter(self, source_path: str) -> list[str]:
        """运行 FR 写的解释器子集，并返回它收集的输出列表。"""
        program_source = f"""
        import "toolchain/lexer.fr";
        import "toolchain/parser.fr";
        import "toolchain/interpreter.fr";
        let actual = runSelfHostedSource(readFile("{source_path}"));
        """
        tokens = Lexer(program_source).scan_tokens()
        program = Parser(tokens).parse()
        interpreter = Interpreter(base_path=Path("examples"))
        interpreter.interpret(program)
        return self.normalize_fr_value(interpreter.globals.values["actual"])

    def run_fr_self_interpreter_result(self, source_path: str) -> dict[str, Any]:
        """运行 FR 写的解释器子集，并返回输出和错误诊断。"""
        program_source = f"""
        import "toolchain/lexer.fr";
        import "toolchain/parser.fr";
        import "toolchain/interpreter.fr";
        let actual = runSelfHostedSourceResult(readFile("{source_path}"));
        """
        tokens = Lexer(program_source).scan_tokens()
        program = Parser(tokens).parse()
        interpreter = Interpreter(base_path=Path("examples"))
        interpreter.interpret(program)
        return self.normalize_fr_value(interpreter.globals.values["actual"])

    def run_legacy_fr_self_interpreter(self, source_path: str) -> list[str]:
        """通过旧 helper 入口运行自解释器，验证兼容导入仍可用。"""
        program_source = f"""
        import "fr_lexer_helpers.fr";
        import "fr_parser_helpers.fr";
        import "fr_interpreter_helpers.fr";
        let actual = runSelfHostedSource(readFile("{source_path}"));
        """
        tokens = Lexer(program_source).scan_tokens()
        program = Parser(tokens).parse()
        interpreter = Interpreter(base_path=Path("examples"))
        interpreter.interpret(program)
        return self.normalize_fr_value(interpreter.globals.values["actual"])

    def python_program_output(self, source_path: str) -> list[str]:
        """运行 Python 实现的 FR 语言链路，并返回输出列表。"""
        source = Path("examples", source_path).read_text(encoding="utf-8")
        tokens = Lexer(source).scan_tokens()
        program = Parser(tokens).parse()
        interpreter = Interpreter(base_path=Path("examples"))
        interpreter.interpret(program)
        return interpreter.output

    def python_parser_ast(self, source_path: str) -> dict[str, Any]:
        """运行 Python Parser，并转换成 FR Parser 子集使用的 AST Map。"""
        source = Path("examples", source_path).read_text(encoding="utf-8")
        tokens = Lexer(source).scan_tokens()
        program = Parser(tokens).parse()
        return self.normalize_python_program(program)

    def normalize_python_program(self, program: Program) -> dict[str, Any]:
        """把 Python Program 节点转换成可对照的字典结构。"""
        return {
            "type": "Program",
            "statements": [
                self.normalize_python_stmt(statement)
                for statement in program.statements
            ],
            "errors": [],
        }

    def normalize_python_stmt(self, statement: Stmt) -> dict[str, Any]:
        """把 Python 语句节点转换成 FR Parser 子集的 AST Map。"""
        if isinstance(statement, VarStmt):
            initializer = None
            if statement.initializer is not None:
                initializer = self.normalize_python_expr(statement.initializer)
            return {
                "type": "VarStmt",
                "name": statement.name.lexeme,
                "initializer": initializer,
            }
        if isinstance(statement, PrintStmt):
            return {
                "type": "PrintStmt",
                "expression": self.normalize_python_expr(statement.expression),
            }
        if isinstance(statement, BlockStmt):
            return {
                "type": "BlockStmt",
                "statements": [
                    self.normalize_python_stmt(child)
                    for child in statement.statements
                ],
            }
        if isinstance(statement, IfStmt):
            else_branch = None
            if statement.else_branch is not None:
                else_branch = self.normalize_python_stmt(statement.else_branch)
            return {
                "type": "IfStmt",
                "condition": self.normalize_python_expr(statement.condition),
                "then_branch": self.normalize_python_stmt(statement.then_branch),
                "else_branch": else_branch,
            }
        if isinstance(statement, WhileStmt):
            return {
                "type": "WhileStmt",
                "condition": self.normalize_python_expr(statement.condition),
                "body": self.normalize_python_stmt(statement.body),
            }
        if isinstance(statement, BreakStmt):
            return {"type": "BreakStmt"}
        if isinstance(statement, FunctionStmt):
            return {
                "type": "FunctionStmt",
                "name": statement.name.lexeme,
                "params": [param.lexeme for param in statement.params],
                "body": [
                    self.normalize_python_stmt(child)
                    for child in statement.body
                ],
            }
        if isinstance(statement, ReturnStmt):
            value = None
            if statement.value is not None:
                value = self.normalize_python_expr(statement.value)
            return {"type": "ReturnStmt", "value": value}
        if isinstance(statement, ExprStmt):
            return {
                "type": "ExprStmt",
                "expression": self.normalize_python_expr(statement.expression),
            }
        self.fail(f"Python AST 语句类型暂未纳入 FR Parser 对照：{type(statement)}")

    def normalize_python_expr(self, expression: Expr) -> dict[str, Any]:
        """把 Python 表达式节点转换成 FR Parser 子集的 AST Map。"""
        if isinstance(expression, LiteralExpr):
            return {"type": "LiteralExpr", "value": expression.value}
        if isinstance(expression, VariableExpr):
            return {"type": "VariableExpr", "name": expression.name.lexeme}
        if isinstance(expression, AssignExpr):
            return {
                "type": "AssignExpr",
                "name": expression.name.lexeme,
                "value": self.normalize_python_expr(expression.value),
            }
        if isinstance(expression, IndexExpr):
            return {
                "type": "IndexExpr",
                "target": self.normalize_python_expr(expression.target),
                "index": self.normalize_python_expr(expression.index),
            }
        if isinstance(expression, IndexAssignExpr):
            return {
                "type": "IndexAssignExpr",
                "target": self.normalize_python_expr(expression.target),
                "index": self.normalize_python_expr(expression.index),
                "value": self.normalize_python_expr(expression.value),
            }
        if isinstance(expression, ListExpr):
            return {
                "type": "ListExpr",
                "elements": [
                    self.normalize_python_expr(element)
                    for element in expression.elements
                ],
            }
        if isinstance(expression, MapExpr):
            return {
                "type": "MapExpr",
                "entries": [
                    {
                        "key": self.normalize_python_expr(entry.key),
                        "value": self.normalize_python_expr(entry.value),
                    }
                    for entry in expression.entries
                ],
            }
        if isinstance(expression, GroupingExpr):
            return {
                "type": "GroupingExpr",
                "expression": self.normalize_python_expr(expression.expression),
            }
        if isinstance(expression, UnaryExpr):
            return {
                "type": "UnaryExpr",
                "operator": expression.operator.lexeme,
                "right": self.normalize_python_expr(expression.right),
            }
        if isinstance(expression, AwaitExpr):
            return {
                "type": "AwaitExpr",
                "expression": self.normalize_python_expr(expression.expression),
            }
        if isinstance(expression, FutureExpr):
            return {
                "type": "FutureExpr",
                "body": [
                    self.normalize_python_stmt(statement)
                    for statement in expression.body
                ],
            }
        if isinstance(expression, BinaryExpr):
            return {
                "type": "BinaryExpr",
                "left": self.normalize_python_expr(expression.left),
                "operator": expression.operator.lexeme,
                "right": self.normalize_python_expr(expression.right),
            }
        if isinstance(expression, CallExpr):
            return {
                "type": "CallExpr",
                "callee": self.normalize_python_expr(expression.callee),
                "arguments": [
                    self.normalize_python_expr(argument)
                    for argument in expression.arguments
                ],
            }
        self.fail(f"Python AST 表达式类型暂未纳入 FR Parser 对照：{type(expression)}")

    def normalize_fr_value(self, value: Any) -> Any:
        """把 FR 运行时的 List/MapKey 结构转换成普通 Python 结构。"""
        if isinstance(value, list):
            return [self.normalize_fr_value(item) for item in value]
        if isinstance(value, dict):
            return {
                self.normalize_fr_key(key): self.normalize_fr_value(item)
                for key, item in value.items()
            }
        return value

    def normalize_fr_key(self, key: Any) -> Any:
        """把解释器内部的 MapKey 还原成用户写下的 key 值。"""
        if isinstance(key, MapKey):
            return key.value
        return key

    def python_lexer_tokens(self, source: str) -> list[dict[str, Any]]:
        """把 Python Lexer 的 Token 转换成和 FR Lexer 相同的字典结构。"""
        return [
            {
                "type": token.type.name,
                "lexeme": token.lexeme,
                "literal": token.literal,
                "line": token.line,
                "column": token.column,
            }
            for token in Lexer(source).scan_tokens()
        ]

    def python_lexer_error_message(self, source: str) -> str:
        """运行 Python Lexer，并返回去掉行列前缀后的核心错误消息。"""
        with self.assertRaises(LexerError) as error_context:
            Lexer(source).scan_tokens()
        return str(error_context.exception).split("：", maxsplit=1)[1]

    def first_error_token(self, source_path: str) -> dict[str, Any]:
        """运行 FR Lexer，并返回它产出的第一个 ERROR Token。"""
        for token in self.run_fr_lexer(source_path):
            if token["type"] == "ERROR":
                return token
        self.fail("FR Lexer 没有产出 ERROR Token")

    def test_fr_lexer_matches_python_lexer_for_basic_source(self) -> None:
        """验证 FR Lexer 在基础源码上和 Python Lexer 输出一致。"""
        source = Path("examples/fr_lexer_sample.fr.txt").read_text(encoding="utf-8")

        self.assertEqual(
            self.run_fr_lexer("fr_lexer_sample.fr.txt"),
            self.python_lexer_tokens(source),
        )

    def test_fr_lexer_matches_python_lexer_for_more_tokens(self) -> None:
        """验证 FR Lexer 在更多符号和字面量上和 Python Lexer 输出一致。"""
        source = Path("examples/fr_lexer_compare_sample.fr.txt").read_text(
            encoding="utf-8"
        )

        self.assertEqual(
            self.run_fr_lexer("fr_lexer_compare_sample.fr.txt"),
            self.python_lexer_tokens(source),
        )

    def test_fr_lexer_matches_python_lexer_for_keywords(self) -> None:
        """验证 FR Lexer 的关键字识别和 Python Lexer 输出一致。"""
        source = Path("examples/fr_lexer_keywords_sample.fr.txt").read_text(
            encoding="utf-8"
        )

        self.assertEqual(
            self.run_fr_lexer("fr_lexer_keywords_sample.fr.txt"),
            self.python_lexer_tokens(source),
        )

    def test_fr_lexer_scans_nil_keyword(self) -> None:
        """验证 FR Lexer 会把 nil 扫描成关键字 Token。"""
        tokens = self.run_fr_lexer("fr_lexer_nil_sample.fr.txt")

        self.assertIn(
            {
                "type": "NIL",
                "lexeme": "nil",
                "literal": None,
                "line": 1,
                "column": 13,
            },
            tokens,
        )

    def test_fr_lexer_matches_python_lexer_for_escaped_strings(self) -> None:
        """验证 FR Lexer 在转义字符串上和 Python Lexer 输出一致。"""
        source = Path("examples/fr_lexer_escaped_string_sample.fr.txt").read_text(
            encoding="utf-8"
        )

        self.assertEqual(
            self.run_fr_lexer("fr_lexer_escaped_string_sample.fr.txt"),
            self.python_lexer_tokens(source),
        )

    def test_fr_lexer_error_token_matches_python_bad_character_error(self) -> None:
        """验证坏字符错误 Token 的核心消息和 Python Lexer 一致。"""
        source = Path("examples/fr_lexer_bad_char_sample.fr.txt").read_text(
            encoding="utf-8"
        )
        error_token = self.first_error_token("fr_lexer_bad_char_sample.fr.txt")

        self.assertEqual(error_token["line"], 1)
        self.assertEqual(error_token["column"], 1)
        self.assertEqual(error_token["lexeme"], "@")
        self.assertEqual(error_token["literal"], self.python_lexer_error_message(source))

    def test_fr_lexer_error_token_matches_python_unterminated_string_error(self) -> None:
        """验证未闭合字符串错误 Token 的核心消息和 Python Lexer 一致。"""
        source = Path("examples/fr_lexer_unterminated_string_sample.fr.txt").read_text(
            encoding="utf-8"
        )
        error_token = self.first_error_token(
            "fr_lexer_unterminated_string_sample.fr.txt"
        )

        self.assertEqual(error_token["line"], 1)
        self.assertEqual(error_token["column"], 1)
        self.assertEqual(error_token["lexeme"], source)
        self.assertEqual(error_token["literal"], self.python_lexer_error_message(source))

    def test_fr_lexer_error_token_matches_python_unknown_escape_error(self) -> None:
        """验证未知字符串转义错误 Token 的核心消息和 Python Lexer 一致。"""
        source = Path("examples/fr_lexer_unknown_escape_sample.fr.txt").read_text(
            encoding="utf-8"
        )
        error_token = self.first_error_token("fr_lexer_unknown_escape_sample.fr.txt")
        expected_lexeme = source.rstrip("\n")[:-1]

        self.assertEqual(error_token["line"], 1)
        self.assertEqual(error_token["column"], 1)
        self.assertEqual(error_token["lexeme"], expected_lexeme)
        self.assertEqual(error_token["literal"], self.python_lexer_error_message(source))

    def test_fr_lexer_demo_scans_keywords_strings_comments_and_symbols(self) -> None:
        """验证 FR 写的 Lexer demo 能扫描更接近真实 FR 源码的 Token。"""
        output = self.run_example("examples/fr_lexer_demo.fr")

        self.assertIn(
            '{"type": "LET", "lexeme": "let", "literal": nil, "line": 2, "column": 1}',
            output,
        )
        self.assertIn(
            '{"type": "IDENTIFIER", "lexeme": "name", "literal": nil, "line": 2, "column": 5}',
            output,
        )
        self.assertIn(
            '{"type": "STRING", "lexeme": ""FR"", "literal": "FR", "line": 2, "column": 12}',
            output,
        )
        self.assertIn(
            '{"type": "IF", "lexeme": "if", "literal": nil, "line": 3, "column": 1}',
            output,
        )
        self.assertIn(
            '{"type": "EQUAL_EQUAL", "lexeme": "==", "literal": nil, "line": 3, "column": 9}',
            output,
        )
        self.assertIn(
            '{"type": "LEFT_BRACE", "lexeme": "{", "literal": nil, "line": 3, "column": 17}',
            output,
        )
        self.assertIn(
            '{"type": "PRINT", "lexeme": "print", "literal": nil, "line": 4, "column": 3}',
            output,
        )
        self.assertNotIn("demo comment", output)
        self.assertTrue(
            output.endswith(
                '{"type": "EOF", "lexeme": "", "literal": nil, "line": 6, "column": 1}]\n'
            )
        )

    def test_fr_lexer_error_demo_reports_error_tokens(self) -> None:
        """验证 FR 写的 Lexer demo 遇到坏字符和未闭合字符串时会产出错误 Token。"""
        output = self.run_example("examples/fr_lexer_error_demo.fr")

        self.assertIn(
            '{"type": "ERROR", "lexeme": "@", "literal": "无法识别的字符：@", "line": 1, "column": 1}',
            output,
        )
        self.assertIn(
            '{"type": "ERROR", "lexeme": ""oops',
            output,
        )
        self.assertIn(
            '"literal": "字符串没有结束", "line": 2, "column": 1}',
            output,
        )

    def test_fr_parser_parses_basic_program_ast(self) -> None:
        """验证 FR Parser 子集能把基础程序解析成 AST Map。"""
        self.assertEqual(
            self.run_fr_parser("fr_parser_basic_sample.fr.txt"),
            {
                "type": "Program",
                "statements": [
                    {
                        "type": "VarStmt",
                        "name": "answer",
                        "initializer": {
                            "type": "BinaryExpr",
                            "left": {"type": "LiteralExpr", "value": 1},
                            "operator": "+",
                            "right": {
                                "type": "BinaryExpr",
                                "left": {"type": "LiteralExpr", "value": 2},
                                "operator": "*",
                                "right": {"type": "LiteralExpr", "value": 3},
                            },
                        },
                    },
                    {
                        "type": "PrintStmt",
                        "expression": {
                            "type": "VariableExpr",
                            "name": "answer",
                        },
                    },
                    {
                        "type": "PrintStmt",
                        "expression": {
                            "type": "BinaryExpr",
                            "left": {"type": "LiteralExpr", "value": None},
                            "operator": "==",
                            "right": {"type": "LiteralExpr", "value": False},
                        },
                    },
                ],
                "errors": [],
            },
        )

    def test_fr_parser_matches_python_parser_for_basic_program(self) -> None:
        """验证 FR Parser 子集和 Python Parser 的 AST 结构一致。"""
        source_path = "fr_parser_basic_sample.fr.txt"

        self.assertEqual(
            self.run_fr_parser(source_path),
            self.python_parser_ast(source_path),
        )

    def test_fr_self_interpreter_runs_basic_program(self) -> None:
        """验证 FR 写的解释器子集能运行基础 FR 程序。"""
        source_path = "fr_parser_basic_sample.fr.txt"

        self.assertEqual(
            self.run_fr_self_interpreter(source_path),
            self.python_program_output(source_path),
        )

    def test_fr_parser_matches_python_parser_for_collection_program(self) -> None:
        """验证 FR Parser 子集能解析集合、索引和赋值 AST。"""
        source_path = "fr_parser_collections_sample.fr.txt"

        self.assertEqual(
            self.run_fr_parser(source_path),
            self.python_parser_ast(source_path),
        )

    def test_fr_self_interpreter_runs_collection_program(self) -> None:
        """验证 FR 写的解释器子集能运行集合和索引程序。"""
        source_path = "fr_parser_collections_sample.fr.txt"

        self.assertEqual(
            self.run_fr_self_interpreter(source_path),
            self.python_program_output(source_path),
        )

    def test_fr_parser_matches_python_parser_for_control_flow_program(self) -> None:
        """验证 FR Parser 子集能解析 if、while 和 block AST。"""
        source_path = "fr_parser_control_flow_sample.fr.txt"

        self.assertEqual(
            self.run_fr_parser(source_path),
            self.python_parser_ast(source_path),
        )

    def test_fr_self_interpreter_runs_control_flow_program(self) -> None:
        """验证 FR 写的解释器子集能运行 if 和 while 程序。"""
        source_path = "fr_parser_control_flow_sample.fr.txt"

        self.assertEqual(
            self.run_fr_self_interpreter(source_path),
            self.python_program_output(source_path),
        )

    def test_fr_parser_matches_python_parser_for_function_program(self) -> None:
        """验证 FR Parser 子集能解析函数声明、调用和 return AST。"""
        source_path = "fr_parser_function_sample.fr.txt"

        self.assertEqual(
            self.run_fr_parser(source_path),
            self.python_parser_ast(source_path),
        )

    def test_fr_self_interpreter_runs_function_program(self) -> None:
        """验证 FR 写的解释器子集能运行函数调用程序。"""
        source_path = "fr_parser_function_sample.fr.txt"

        self.assertEqual(
            self.run_fr_self_interpreter(source_path),
            self.python_program_output(source_path),
        )

    def test_fr_parser_matches_python_parser_for_scope_program(self) -> None:
        """验证 FR Parser 子集能解析作用域和跨函数调用样例 AST。"""
        source_path = "fr_parser_scope_sample.fr.txt"

        self.assertEqual(
            self.run_fr_parser(source_path),
            self.python_parser_ast(source_path),
        )

    def test_fr_self_interpreter_runs_scope_program(self) -> None:
        """验证 FR 写的解释器子集能处理 block 作用域和全局读取。"""
        source_path = "fr_parser_scope_sample.fr.txt"

        self.assertEqual(
            self.run_fr_self_interpreter(source_path),
            self.python_program_output(source_path),
        )

    def test_fr_parser_matches_python_parser_for_logic_program(self) -> None:
        """验证 FR Parser 子集能解析 and/or 逻辑表达式 AST。"""
        source_path = "fr_parser_logic_sample.fr.txt"

        self.assertEqual(
            self.run_fr_parser(source_path),
            self.python_parser_ast(source_path),
        )

    def test_fr_self_interpreter_runs_logic_program(self) -> None:
        """验证 FR 写的解释器子集能按短路规则执行 and/or。"""
        source_path = "fr_parser_logic_sample.fr.txt"

        self.assertEqual(
            self.run_fr_self_interpreter(source_path),
            self.python_program_output(source_path),
        )

    def test_fr_parser_matches_python_parser_for_break_program(self) -> None:
        """验证 FR Parser 子集能解析 break 语句 AST。"""
        source_path = "fr_parser_break_sample.fr.txt"

        self.assertEqual(
            self.run_fr_parser(source_path),
            self.python_parser_ast(source_path),
        )

    def test_fr_self_interpreter_runs_break_program(self) -> None:
        """验证 FR 写的解释器子集能在 while 中处理 break。"""
        source_path = "fr_parser_break_sample.fr.txt"

        self.assertEqual(
            self.run_fr_self_interpreter(source_path),
            self.python_program_output(source_path),
        )

    def test_fr_parser_matches_python_parser_for_future_program(self) -> None:
        """验证 FR Parser 子集能解析 future 和 await AST。"""
        source_path = "fr_parser_future_sample.fr.txt"

        self.assertEqual(
            self.run_fr_parser(source_path),
            self.python_parser_ast(source_path),
        )

    def test_fr_self_interpreter_runs_future_program(self) -> None:
        """验证 FR 写的解释器子集能延迟执行并 await Future。"""
        source_path = "fr_parser_future_sample.fr.txt"

        self.assertEqual(
            self.run_fr_self_interpreter(source_path),
            self.python_program_output(source_path),
        )

    def test_fr_parser_matches_python_parser_for_builtins_program(self) -> None:
        """验证 FR Parser 子集能解析调用内置函数的程序 AST。"""
        source_path = "fr_parser_builtins_sample.fr.txt"

        self.assertEqual(
            self.run_fr_parser(source_path),
            self.python_parser_ast(source_path),
        )

    def test_fr_self_interpreter_runs_builtins_program(self) -> None:
        """验证 FR 写的解释器子集能桥接常用内置函数。"""
        source_path = "fr_parser_builtins_sample.fr.txt"

        self.assertEqual(
            self.run_fr_self_interpreter(source_path),
            self.python_program_output(source_path),
        )

    def test_legacy_fr_toolchain_helper_imports_still_work(self) -> None:
        """验证旧 helper 文件仍会导入新的 toolchain 组件。"""
        source_path = "fr_parser_basic_sample.fr.txt"

        self.assertEqual(
            self.run_legacy_fr_self_interpreter(source_path),
            self.python_program_output(source_path),
        )

    def test_fr_self_interpreter_reports_basic_runtime_errors(self) -> None:
        """验证 FR 写的解释器子集能记录基础运行时错误。"""
        result = self.run_fr_self_interpreter_result("fr_parser_error_sample.fr.txt")
        messages = [error["message"] for error in result["errors"]]

        self.assertEqual(
            messages,
            [
                "变量 missing 未定义",
                "只能调用函数",
                "await 只能用于 Future",
            ],
        )

    def test_fr_self_interpreter_reports_invalid_top_level_return(self) -> None:
        """验证顶层 return 会被自解释器记录为非法控制流。"""
        result = self.run_fr_self_interpreter_result(
            "fr_parser_top_level_return_error_sample.fr.txt"
        )

        self.assertEqual(
            [error["message"] for error in result["errors"]],
            ["return 只能用于函数"],
        )

    def test_fr_self_interpreter_reports_invalid_top_level_break(self) -> None:
        """验证顶层 break 会被自解释器记录为非法控制流。"""
        result = self.run_fr_self_interpreter_result(
            "fr_parser_top_level_break_error_sample.fr.txt"
        )

        self.assertEqual(
            [error["message"] for error in result["errors"]],
            ["break 只能用于 while 循环"],
        )

    def test_fr_self_interpreter_reports_invalid_function_break(self) -> None:
        """验证函数中未被 while 捕获的 break 会记录错误。"""
        result = self.run_fr_self_interpreter_result(
            "fr_parser_function_break_error_sample.fr.txt"
        )

        self.assertEqual(
            [error["message"] for error in result["errors"]],
            ["break 只能用于 while 循环"],
        )

    def test_fr_self_interpreter_reports_invalid_future_break(self) -> None:
        """验证 Future 中未被 while 捕获的 break 会记录错误。"""
        result = self.run_fr_self_interpreter_result(
            "fr_parser_future_break_error_sample.fr.txt"
        )

        self.assertEqual(
            [error["message"] for error in result["errors"]],
            ["break 只能用于 while 循环"],
        )


if __name__ == "__main__":
    unittest.main()
