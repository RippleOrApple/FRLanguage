import io
import unittest
from contextlib import redirect_stdout

from frlang.main import main


class ExampleTest(unittest.TestCase):
    """验证 examples 目录中的 FR 示例程序仍然可以作为学习材料运行。"""

    def run_example(self, path: str) -> str:
        """运行一个示例文件，并返回它打印到标准输出的文本。"""
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            main([path])
        return stdout.getvalue()

    def test_fr_lexer_demo_scans_keywords_strings_comments_and_symbols(self) -> None:
        """验证 FR 写的 Lexer demo 能扫描更接近真实 FR 源码的 Token。"""
        output = self.run_example("examples/fr_lexer_demo.fr")

        self.assertIn(
            '{"type": "LET", "lexeme": "let", "literal": nil, "line": 2, "column": 1}',
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
