import unittest

from frlang.errors import RuntimeError
from frlang.ast import Program
from frlang.interpreter import Interpreter
from frlang.lexer import Lexer
from frlang.parser import Parser


class InterpreterTest(unittest.TestCase):
    def run_source(self, source: str) -> Interpreter:
        tokens = Lexer(source).scan_tokens()
        program = Parser(tokens).parse()
        interpreter = Interpreter()
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


if __name__ == "__main__":
    unittest.main()
