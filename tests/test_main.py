import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from frlang.main import main


class MainTest(unittest.TestCase):
    def test_main_runs_source_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "program.fr"
            source_path.write_text("let x = 1 + 2 * 3;\nprint(x);\n", encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main([str(source_path)])

        self.assertEqual(stdout.getvalue(), "7\n")

    def test_main_resolves_read_file_from_source_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "program.fr"
            data_path = Path(directory) / "data.txt"
            data_path.write_text("from sibling file", encoding="utf-8")
            source_path.write_text('print(readFile("data.txt"));\n', encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main([str(source_path)])

        self.assertEqual(stdout.getvalue(), "from sibling file\n")

    def test_main_reports_language_error_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "program.fr"
            source_path.write_text("print(missing);\n", encoding="utf-8")

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as exit_context:
                    main([str(source_path)])

        self.assertEqual(exit_context.exception.code, 70)
        self.assertIn("错误：", stderr.getvalue())
        self.assertIn("变量 missing 未定义", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_main_reports_missing_file_without_traceback(self) -> None:
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as exit_context:
                main(["missing.fr"])

        self.assertEqual(exit_context.exception.code, 66)
        self.assertIn("文件读取失败：missing.fr", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
