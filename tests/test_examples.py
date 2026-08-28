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

        self.assertIn('{"type": "LET", "lexeme": "let"}', output)
        self.assertIn('{"type": "STRING"', output)
        self.assertIn('{"type": "IF", "lexeme": "if"}', output)
        self.assertIn('{"type": "EQUAL_EQUAL", "lexeme": "=="}', output)
        self.assertIn('{"type": "LEFT_BRACE", "lexeme": "{"}', output)
        self.assertIn('{"type": "PRINT", "lexeme": "print"}', output)
        self.assertNotIn("demo comment", output)
        self.assertTrue(output.endswith('{"type": "EOF", "lexeme": ""}]\n'))


if __name__ == "__main__":
    unittest.main()
