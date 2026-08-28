import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

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
        import "fr_lexer_helpers.fr";
        let actual = scan(readFile("{source_path}"));
        """
        tokens = Lexer(program_source).scan_tokens()
        program = Parser(tokens).parse()
        interpreter = Interpreter(base_path=Path("examples"))
        interpreter.interpret(program)
        return self.normalize_fr_value(interpreter.globals.values["actual"])

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
            '{"type": "ERROR", "lexeme": "@", "literal": "无法识别的字符", "line": 1, "column": 1}',
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


if __name__ == "__main__":
    unittest.main()
