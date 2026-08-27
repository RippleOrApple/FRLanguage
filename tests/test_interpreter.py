import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from frlang.errors import RuntimeError
from frlang.ast import Program
from frlang.interpreter import Interpreter
from frlang.lexer import Lexer
from frlang.parser import Parser


class InterpreterTest(unittest.TestCase):
    def run_source(self, source: str, **interpreter_options: Any) -> Interpreter:
        tokens = Lexer(source).scan_tokens()
        program = Parser(tokens).parse()
        interpreter = Interpreter(**interpreter_options)
        interpreter.interpret(program)
        return interpreter

    def test_empty_program_runs_without_error(self) -> None:
        Interpreter().interpret(Program(statements=[]))

    def test_runs_variable_declaration_and_print(self) -> None:
        interpreter = self.run_source(
            """
            let x = 1 + 2 * 3;
            print(x);
            """
        )

        self.assertEqual(interpreter.output, ["7"])

    def test_runs_grouping_unary_and_comparison(self) -> None:
        interpreter = self.run_source(
            """
            print((1 + 2) * -3);
            print(3 * 3 == 9);
            print(!false);
            """
        )

        self.assertEqual(interpreter.output, ["-9", "true", "true"])

    def test_raises_runtime_error_for_undefined_variable(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "变量 missing 未定义"):
            self.run_source("print(missing);")

    def test_runs_assignment(self) -> None:
        interpreter = self.run_source(
            """
            let x = 1;
            x = x + 2;
            print(x);
            """
        )

        self.assertEqual(interpreter.output, ["3"])

    def test_runs_block_with_local_scope(self) -> None:
        interpreter = self.run_source(
            """
            let x = "outer";
            {
              let x = "inner";
              print(x);
            }
            print(x);
            """
        )

        self.assertEqual(interpreter.output, ["inner", "outer"])

    def test_runs_while_loop(self) -> None:
        interpreter = self.run_source(
            """
            let i = 0;
            while i < 3 {
              print(i);
              i = i + 1;
            }
            """
        )

        self.assertEqual(interpreter.output, ["0", "1", "2"])

    def test_break_exits_nearest_while_loop(self) -> None:
        interpreter = self.run_source(
            """
            let i = 0;
            while i < 5 {
              if i == 3 {
                break;
              }
              print(i);
              i = i + 1;
            }
            print("done");
            """
        )

        self.assertEqual(interpreter.output, ["0", "1", "2", "done"])

    def test_break_outside_while_raises_runtime_error(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "break 只能用于 while 循环"):
            self.run_source("break;")

    def test_break_cannot_escape_function_boundary(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "break 只能用于 while 循环"):
            self.run_source(
                """
                fn stop() {
                  break;
                }

                while true {
                  stop();
                }
                """
            )

    def test_import_runs_relative_file_and_exposes_definitions(self) -> None:
        with TemporaryDirectory() as directory:
            base_path = Path(directory)
            (base_path / "helper.fr").write_text(
                """
                fn addOne(value) {
                  return value + 1;
                }
                """,
                encoding="utf-8",
            )
            interpreter = self.run_source(
                """
                import "helper.fr";
                print(addOne(41));
                """,
                base_path=base_path,
            )

        self.assertEqual(interpreter.output, ["42"])

    def test_import_executes_each_file_once(self) -> None:
        with TemporaryDirectory() as directory:
            base_path = Path(directory)
            (base_path / "helper.fr").write_text(
                """
                print("loading");
                fn label() {
                  return "ok";
                }
                """,
                encoding="utf-8",
            )
            interpreter = self.run_source(
                """
                import "helper.fr";
                import "helper.fr";
                print(label());
                """,
                base_path=base_path,
            )

        self.assertEqual(interpreter.output, ["loading", "ok"])

    def test_import_rejects_unsafe_paths(self) -> None:
        with TemporaryDirectory() as directory:
            base_path = Path(directory)
            with self.assertRaisesRegex(RuntimeError, "import 只支持相对路径"):
                self.run_source(
                    f'import "{base_path.resolve()}";',
                    base_path=base_path,
                )

            with self.assertRaisesRegex(RuntimeError, "import 不能读取工作目录外的文件"):
                self.run_source('import "../outside.fr";', base_path=base_path)

    def test_runs_if_then_branch(self) -> None:
        interpreter = self.run_source(
            """
            let score = 90;
            if score >= 60 {
              print("pass");
            } else {
              print("fail");
            }
            """
        )

        self.assertEqual(interpreter.output, ["pass"])

    def test_runs_if_else_branch(self) -> None:
        interpreter = self.run_source(
            """
            let score = 30;
            if score >= 60 {
              print("pass");
            } else {
              print("fail");
            }
            """
        )

        self.assertEqual(interpreter.output, ["fail"])

    def test_skips_if_without_else_when_condition_is_false(self) -> None:
        interpreter = self.run_source(
            """
            if false {
              print("hidden");
            }
            print("done");
            """
        )

        self.assertEqual(interpreter.output, ["done"])

    def test_runs_logical_and_or_with_short_circuit(self) -> None:
        interpreter = self.run_source(
            """
            print(true or missing);
            print(false and missing);
            print(false or "fallback");
            print("value" and 123);
            """
        )

        self.assertEqual(interpreter.output, ["true", "false", "fallback", "123"])

    def test_calls_function_with_return_value(self) -> None:
        interpreter = self.run_source(
            """
            fn add(a, b) {
              return a + b;
            }

            print(add(1, 2));
            """
        )

        self.assertEqual(interpreter.output, ["3"])

    def test_function_uses_local_scope(self) -> None:
        interpreter = self.run_source(
            """
            let value = "outer";

            fn show(value) {
              print(value);
              return value;
            }

            print(show("inner"));
            print(value);
            """
        )

        self.assertEqual(interpreter.output, ["inner", "inner", "outer"])

    def test_calls_recursive_function(self) -> None:
        interpreter = self.run_source(
            """
            fn fact(n) {
              if n <= 1 {
                return 1;
              }

              return n * fact(n - 1);
            }

            print(fact(5));
            """
        )

        self.assertEqual(interpreter.output, ["120"])

    def test_awaits_future_block_value(self) -> None:
        interpreter = self.run_source(
            """
            let value = await future {
              return 21 * 2;
            };

            print(value);
            """
        )

        self.assertEqual(interpreter.output, ["42"])

    def test_awaits_future_returned_from_function(self) -> None:
        interpreter = self.run_source(
            """
            fn later(x) {
              return future {
                return x + 1;
              };
            }

            print(await later(41));
            """
        )

        self.assertEqual(interpreter.output, ["42"])

    def test_await_requires_future(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "await 只能用于 Future"):
            self.run_source("print(await 1);")

    def test_future_block_runs_when_awaited(self) -> None:
        interpreter = self.run_source(
            """
            let value = future {
              print("future");
              return 42;
            };

            print("before");
            print(await value);
            """
        )

        self.assertEqual(interpreter.output, ["before", "future", "42"])

    def test_prints_list_literal(self) -> None:
        interpreter = self.run_source("print([1, 2, 3]);")

        self.assertEqual(interpreter.output, ["[1, 2, 3]"])

    def test_reads_list_index(self) -> None:
        interpreter = self.run_source(
            """
            let items = ["first", "second", "third"];
            print(items[1]);
            """
        )

        self.assertEqual(interpreter.output, ["second"])

    def test_assigns_list_index(self) -> None:
        interpreter = self.run_source(
            """
            let items = [1, 2, 3];
            items[1] = 42;
            print(items[1]);
            print(items);
            """
        )

        self.assertEqual(interpreter.output, ["42", "[1, 42, 3]"])

    def test_list_index_must_be_number(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "列表索引必须是数字"):
            self.run_source('print([1, 2]["bad"]);')

    def test_list_index_out_of_range_raises_runtime_error(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "列表索引越界"):
            self.run_source("print([1, 2][2]);")

    def test_prints_map_literal(self) -> None:
        interpreter = self.run_source('print({"name": "FR", "version": 1});')

        self.assertEqual(interpreter.output, ['{"name": "FR", "version": 1}'])

    def test_reads_map_key(self) -> None:
        interpreter = self.run_source(
            """
            let user = {"name": "FR", "version": 1};
            print(user["name"]);
            """
        )

        self.assertEqual(interpreter.output, ["FR"])

    def test_assigns_map_key(self) -> None:
        interpreter = self.run_source(
            """
            let user = {"name": "FR", "version": 1};
            user["version"] = 2;
            print(user);
            """
        )

        self.assertEqual(interpreter.output, ['{"name": "FR", "version": 2}'])

    def test_map_keeps_boolean_and_number_keys_separate(self) -> None:
        interpreter = self.run_source(
            """
            let values = {true: "yes", 1: "one"};
            print(values[true]);
            print(values[1]);
            """
        )

        self.assertEqual(interpreter.output, ["yes", "one"])

    def test_map_key_must_be_hashable_value(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "Map key 类型不支持"):
            self.run_source('print({"name": "FR"}[[1]]);')

    def test_missing_map_key_raises_runtime_error(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "Map key 不存在"):
            self.run_source('print({"name": "FR"}["missing"]);')

    def test_builtin_len_reads_string_list_and_map_size(self) -> None:
        interpreter = self.run_source(
            """
            print(len("hello"));
            print(len([1, 2, 3]));
            print(len({"name": "FR", "version": 1}));
            """
        )

        self.assertEqual(interpreter.output, ["5", "3", "2"])

    def test_builtin_string_helpers_read_text_parts(self) -> None:
        interpreter = self.run_source(
            """
            print(charAt("hello", 1));
            print(substring("hello", 1, 4));
            """
        )

        self.assertEqual(interpreter.output, ["e", "ell"])

    def test_builtin_type_str_and_number_convert_values(self) -> None:
        interpreter = self.run_source(
            """
            let missing;
            print(type(123));
            print(type("FR"));
            print(type([1]));
            print(type({"ok": true}));
            print(type(missing));
            print(str(42) + "!");
            print(number("41") + 1);
            """
        )

        self.assertEqual(
            interpreter.output,
            ["number", "string", "list", "map", "nil", "42!", "42"],
        )

    def test_builtin_push_and_pop_mutate_list(self) -> None:
        interpreter = self.run_source(
            """
            let items = [1];
            print(push(items, 2));
            print(items);
            print(pop(items));
            print(items);
            """
        )

        self.assertEqual(interpreter.output, ["2", "[1, 2]", "2", "[1]"])

    def test_builtin_reports_argument_type_errors(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "len 参数必须是字符串、List 或 Map"):
            self.run_source("print(len(1));")

        with self.assertRaisesRegex(RuntimeError, "charAt 第 2 个参数必须是整数"):
            self.run_source('print(charAt("hello", "1"));')

        with self.assertRaisesRegex(RuntimeError, "number 无法转换这个字符串"):
            self.run_source('print(number("abc"));')

    def test_builtin_read_file_reads_relative_text_file(self) -> None:
        with TemporaryDirectory() as directory:
            base_path = Path(directory)
            (base_path / "data.txt").write_text("hello\nFR", encoding="utf-8")
            interpreter = self.run_source(
                'print(readFile("data.txt"));',
                base_path=base_path,
            )

        self.assertEqual(interpreter.output, ["hello\nFR"])

    def test_builtin_read_file_rejects_unsafe_paths(self) -> None:
        with TemporaryDirectory() as directory:
            base_path = Path(directory)
            with self.assertRaisesRegex(RuntimeError, "readFile 只支持相对路径"):
                self.run_source(
                    f'print(readFile("{base_path.resolve()}"));',
                    base_path=base_path,
                )

            with self.assertRaisesRegex(RuntimeError, "readFile 不能读取工作目录外的文件"):
                self.run_source('print(readFile("../outside.txt"));', base_path=base_path)


if __name__ == "__main__":
    unittest.main()
