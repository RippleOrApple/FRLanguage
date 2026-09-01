"""解释器核心。"""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .ast import (
    AssignExpr,
    AwaitExpr,
    BinaryExpr,
    BlockStmt,
    BreakStmt,
    CallExpr,
    Expr,
    ExprStmt,
    FunctionStmt,
    FutureExpr,
    GroupingExpr,
    IfStmt,
    ImportStmt,
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
from .environment import Environment
from .errors import FRLanguageError
from .errors import RuntimeError as FRRuntimeError
from .future import Future, FutureState
from .runtime import Runtime
from .token import Token, TokenType


class ReturnSignal(Exception):
    """函数 return 使用的内部控制流信号。"""

    def __init__(self, value: Any) -> None:
        """保存 return 后面的值，交给函数调用边界处理。"""
        self.value = value


class BreakSignal(Exception):
    """break 使用的内部控制流信号。"""

    def __init__(self, keyword: Token) -> None:
        """保存 break 关键字位置，便于非法使用时输出准确行列号。"""
        self.keyword = keyword


@dataclass(frozen=True)
class MapKey:
    """Map 运行时使用的内部 key，避免 true 和 1 在 Python dict 中混淆。"""

    kind: str
    value: Any


class FRFunction:
    """FRLanguage 函数对象。"""

    def __init__(self, declaration: FunctionStmt, closure: Environment) -> None:
        """保存函数声明和声明时的外层环境。

        `closure` 让函数调用时仍能访问定义位置附近的变量，递归函数也依赖这个环境模型。
        """
        self.declaration = declaration
        self.closure = closure

    def call(
        self,
        interpreter: "Interpreter",
        arguments: list[Any],
        call_token: Token,
    ) -> Any:
        """调用用户用 FR 写的函数。

        每次调用都会创建新的局部环境，把参数名绑定到实参值，然后执行函数体。
        `return` 通过 ReturnSignal 提前离开函数体。
        """
        environment = Environment(self.closure)
        for param, argument in zip(self.declaration.params, arguments):
            environment.define(param.lexeme, argument)

        try:
            interpreter.execute_block(self.declaration.body, environment)
        except ReturnSignal as signal:
            return signal.value
        except BreakSignal as signal:
            interpreter.raise_runtime_error(signal.keyword, "break 只能用于 while 循环")

        return None

    def arity(self) -> int:
        """返回函数需要的参数数量。"""
        return len(self.declaration.params)

    def __str__(self) -> str:
        """返回调试用的函数显示文本。"""
        return f"<fn {self.declaration.name.lexeme}>"


class FRNativeFunction:
    """由 Python 实现、暴露给 FRLanguage 的原生函数。"""

    def __init__(
        self,
        name: str,
        arity: int,
        function: Callable[["Interpreter", list[Any], Token], Any],
    ) -> None:
        """创建一个由 Python 实现的 FR 原生函数。"""
        self.name = name
        self._arity = arity
        self.function = function

    def call(
        self,
        interpreter: "Interpreter",
        arguments: list[Any],
        call_token: Token,
    ) -> Any:
        """调用原生函数实现。"""
        return self.function(interpreter, arguments, call_token)

    def arity(self) -> int:
        """返回原生函数需要的参数数量。"""
        return self._arity

    def __str__(self) -> str:
        """返回调试用的原生函数显示文本。"""
        return f"<native fn {self.name}>"


class Interpreter:
    """执行 FRLanguage AST。"""

    def __init__(self, base_path: Path | str | None = None) -> None:
        """初始化解释器状态。

        `globals` 保存全局变量和内置函数，`environment` 指向当前作用域。
        `base_path` 是 `readFile` 和 `import` 解析相对路径的起点。
        """
        self.ensure_recursion_capacity()
        self.globals = Environment()
        self.environment = self.globals
        self.runtime = Runtime()
        self.output: list[str] = []
        self.base_path = Path.cwd() if base_path is None else Path(base_path)
        self.imported_paths: set[Path] = set()
        self.define_native_functions()

    @staticmethod
    def ensure_recursion_capacity() -> None:
        """为自举实验提高宿主递归承载能力。"""
        minimum_limit = 10000
        if sys.getrecursionlimit() < minimum_limit:
            sys.setrecursionlimit(minimum_limit)

    def interpret(self, program: Program) -> None:
        """执行程序。"""
        for statement in program.statements:
            try:
                self.execute(statement)
            except BreakSignal as signal:
                self.raise_runtime_error(signal.keyword, "break 只能用于 while 循环")

    def execute(self, statement: Stmt) -> None:
        """执行一条语句节点。

        语句通常产生副作用或控制流变化，例如定义变量、输出、循环、导入和 return。
        """
        if isinstance(statement, VarStmt):
            value = None
            if statement.initializer is not None:
                value = self.evaluate(statement.initializer)
            self.environment.define(statement.name.lexeme, value)
            return

        if isinstance(statement, ImportStmt):
            self.execute_import(statement)
            return

        if isinstance(statement, FunctionStmt):
            function = FRFunction(statement, self.environment)
            self.environment.define(statement.name.lexeme, function)
            return

        if isinstance(statement, PrintStmt):
            value = self.evaluate(statement.expression)
            self.output.append(self.stringify(value))
            return

        if isinstance(statement, ExprStmt):
            self.evaluate(statement.expression)
            return

        if isinstance(statement, BlockStmt):
            self.execute_block(statement.statements, Environment(self.environment))
            return

        if isinstance(statement, WhileStmt):
            while self.is_truthy(self.evaluate(statement.condition)):
                try:
                    self.execute(statement.body)
                except BreakSignal:
                    break
            return

        if isinstance(statement, BreakStmt):
            raise BreakSignal(statement.keyword)

        if isinstance(statement, IfStmt):
            if self.is_truthy(self.evaluate(statement.condition)):
                self.execute(statement.then_branch)
            elif statement.else_branch is not None:
                self.execute(statement.else_branch)
            return

        if isinstance(statement, ReturnStmt):
            value = None
            if statement.value is not None:
                value = self.evaluate(statement.value)
            raise ReturnSignal(value)

        raise FRRuntimeError(f"不支持的语句类型：{type(statement).__name__}")

    def execute_block(self, statements: list[Stmt], environment: Environment) -> None:
        """在新的局部环境中执行一组语句。

        执行结束后必须恢复旧环境；即使中途 return/break/报错，也要保证作用域不会泄漏。
        """
        previous = self.environment
        try:
            self.environment = environment
            for statement in statements:
                self.execute(statement)
        finally:
            self.environment = previous

    def execute_import(self, statement: ImportStmt) -> None:
        """执行 `import "file.fr";`。

        导入文件复用当前解释器和全局环境，因此 helper 文件里的函数能被主文件继续调用。
        `imported_paths` 防止同一个文件被重复执行。
        """
        target_path = self.resolve_relative_path(
            statement.path,
            statement.path.literal,
            "import",
        )
        if target_path in self.imported_paths:
            return

        self.imported_paths.add(target_path)
        try:
            source = target_path.read_text(encoding="utf-8")
        except OSError as error:
            self.raise_runtime_error(statement.path, f"import 读取失败：{error}")

        from .lexer import Lexer
        from .parser import Parser

        previous_base_path = self.base_path
        try:
            tokens = Lexer(source).scan_tokens()
            program = Parser(tokens).parse()
            self.base_path = target_path.parent
            self.interpret(program)
        except FRLanguageError as error:
            self.imported_paths.discard(target_path)
            self.raise_runtime_error(
                statement.path,
                f'导入 "{statement.path.literal}" 时出错：{error}',
            )
        finally:
            self.base_path = previous_base_path

    def evaluate(self, expression: Expr) -> Any:
        """计算表达式节点并返回运行时值。

        表达式会产生值，例如数字、字符串、函数调用结果、List、Map 或 Future。
        """
        if isinstance(expression, LiteralExpr):
            return expression.value

        if isinstance(expression, ListExpr):
            return [self.evaluate(element) for element in expression.elements]

        if isinstance(expression, MapExpr):
            values: dict[Any, Any] = {}
            for entry in expression.entries:
                key = self.evaluate(entry.key)
                normalized_key = self.normalize_map_key(expression=entry.key, key=key)
                values[normalized_key] = self.evaluate(entry.value)
            return values

        if isinstance(expression, VariableExpr):
            return self.environment.get(expression.name)

        if isinstance(expression, AssignExpr):
            value = self.evaluate(expression.value)
            self.environment.assign(expression.name, value)
            return value

        if isinstance(expression, IndexAssignExpr):
            target = self.evaluate(expression.target)
            index = self.evaluate(expression.index)
            value = self.evaluate(expression.value)
            if isinstance(target, list):
                normalized_index = self.normalize_list_index(expression.bracket, index)
                self.check_list_index_range(expression.bracket, target, normalized_index)
                target[normalized_index] = value
                return value
            if isinstance(target, dict):
                normalized_key = self.normalize_map_key_token(expression.bracket, index)
                target[normalized_key] = value
                return value
            self.raise_runtime_error(expression.bracket, "只能给 List 或 Map 索引赋值")
            return value

        if isinstance(expression, GroupingExpr):
            return self.evaluate(expression.expression)

        if isinstance(expression, CallExpr):
            callee = self.evaluate(expression.callee)
            arguments = [self.evaluate(argument) for argument in expression.arguments]

            if not isinstance(callee, (FRFunction, FRNativeFunction)):
                self.raise_runtime_error(expression.paren, "只能调用函数")

            if len(arguments) != callee.arity():
                self.raise_runtime_error(
                    expression.paren,
                    f"参数数量不匹配：需要 {callee.arity()} 个，实际 {len(arguments)} 个",
                )

            return callee.call(self, arguments, expression.paren)

        if isinstance(expression, FutureExpr):
            future = Future()
            closure = self.environment

            def run_future_block() -> None:
                """在 Runtime 队列中执行 future 块，并把结果写回 Future。"""
                try:
                    self.execute_block(expression.body, Environment(closure))
                except ReturnSignal as signal:
                    future.resolve(signal.value)
                except BreakSignal as signal:
                    future.reject(
                        FRRuntimeError(
                            f"第 {signal.keyword.line} 行，第 {signal.keyword.column} 列：break 只能用于 while 循环"
                        )
                    )
                except FRRuntimeError as error:
                    future.reject(error)
                else:
                    future.resolve(None)

            self.runtime.schedule(run_future_block)
            return future

        if isinstance(expression, AwaitExpr):
            future = self.evaluate(expression.expression)
            if not isinstance(future, Future):
                self.raise_runtime_error(expression.keyword, "await 只能用于 Future")

            if future.state is FutureState.PENDING:
                self.runtime.run_until_future(future)

            if future.state is FutureState.RESOLVED:
                return future.value
            if future.state is FutureState.REJECTED:
                if isinstance(future.error, FRRuntimeError):
                    raise future.error
                self.raise_runtime_error(expression.keyword, "Future 执行失败")

            self.raise_runtime_error(expression.keyword, "Future 尚未完成")

        if isinstance(expression, IndexExpr):
            target = self.evaluate(expression.target)
            index = self.evaluate(expression.index)
            if isinstance(target, list):
                normalized_index = self.normalize_list_index(expression.bracket, index)
                self.check_list_index_range(expression.bracket, target, normalized_index)
                return target[normalized_index]
            if isinstance(target, dict):
                normalized_key = self.normalize_map_key_token(expression.bracket, index)
                if normalized_key not in target:
                    self.raise_runtime_error(expression.bracket, "Map key 不存在")
                return target[normalized_key]
            self.raise_runtime_error(expression.bracket, "只能读取 List 或 Map 索引")

        if isinstance(expression, UnaryExpr):
            right = self.evaluate(expression.right)
            if expression.operator.type is TokenType.MINUS:
                self.check_number_operand(expression.operator, right)
                return -right
            if expression.operator.type is TokenType.BANG:
                return not self.is_truthy(right)

        if isinstance(expression, BinaryExpr):
            left = self.evaluate(expression.left)
            operator_type = expression.operator.type

            if operator_type is TokenType.OR:
                if self.is_truthy(left):
                    return left
                return self.evaluate(expression.right)

            if operator_type is TokenType.AND:
                if not self.is_truthy(left):
                    return left
                return self.evaluate(expression.right)

            right = self.evaluate(expression.right)

            if operator_type is TokenType.PLUS:
                if self.are_numbers(left, right) or (
                    isinstance(left, str) and isinstance(right, str)
                ):
                    return left + right
                self.raise_runtime_error(expression.operator, "'+' 两边类型不匹配")

            if operator_type is TokenType.MINUS:
                self.check_number_operands(expression.operator, left, right)
                return left - right

            if operator_type is TokenType.STAR:
                self.check_number_operands(expression.operator, left, right)
                return left * right

            if operator_type is TokenType.SLASH:
                self.check_number_operands(expression.operator, left, right)
                if right == 0:
                    self.raise_runtime_error(expression.operator, "不能除以 0")
                return left / right

            if operator_type is TokenType.GREATER:
                self.check_number_operands(expression.operator, left, right)
                return left > right

            if operator_type is TokenType.GREATER_EQUAL:
                self.check_number_operands(expression.operator, left, right)
                return left >= right

            if operator_type is TokenType.LESS:
                self.check_number_operands(expression.operator, left, right)
                return left < right

            if operator_type is TokenType.LESS_EQUAL:
                self.check_number_operands(expression.operator, left, right)
                return left <= right

            if operator_type is TokenType.EQUAL_EQUAL:
                return left == right

            if operator_type is TokenType.BANG_EQUAL:
                return left != right

        raise FRRuntimeError(f"不支持的表达式类型：{type(expression).__name__}")

    @staticmethod
    def is_truthy(value: Any) -> bool:
        """按照 FR 的规则判断一个值是否为真。

        当前只有 nil 和 false 为假，其他值都按真处理。
        """
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        return True

    def define_native_functions(self) -> None:
        """把内置函数注册到全局环境。"""
        natives = [
            FRNativeFunction("len", 1, Interpreter.native_len),
            FRNativeFunction("charAt", 2, Interpreter.native_char_at),
            FRNativeFunction("substring", 3, Interpreter.native_substring),
            FRNativeFunction("isDigit", 1, Interpreter.native_is_digit),
            FRNativeFunction("isAlpha", 1, Interpreter.native_is_alpha),
            FRNativeFunction("isAlphaNumeric", 1, Interpreter.native_is_alpha_numeric),
            FRNativeFunction("codePoint", 1, Interpreter.native_code_point),
            FRNativeFunction("type", 1, Interpreter.native_type),
            FRNativeFunction("str", 1, Interpreter.native_str),
            FRNativeFunction("number", 1, Interpreter.native_number),
            FRNativeFunction("hasKey", 2, Interpreter.native_has_key),
            FRNativeFunction("push", 2, Interpreter.native_push),
            FRNativeFunction("pop", 1, Interpreter.native_pop),
            FRNativeFunction("readFile", 1, Interpreter.native_read_file),
        ]
        for native in natives:
            self.globals.define(native.name, native)

    @staticmethod
    def native_len(interpreter: "Interpreter", arguments: list[Any], token: Token) -> int:
        """实现 `len(value)`：读取字符串、List 或 Map 的长度。"""
        value = arguments[0]
        if isinstance(value, (str, list, dict)):
            return len(value)
        interpreter.raise_runtime_error(token, "len 参数必须是字符串、List 或 Map")

    @staticmethod
    def native_char_at(
        interpreter: "Interpreter",
        arguments: list[Any],
        token: Token,
    ) -> str:
        """实现 `charAt(text, index)`：读取字符串指定位置字符。"""
        text = arguments[0]
        index = arguments[1]
        if not isinstance(text, str):
            interpreter.raise_runtime_error(token, "charAt 第 1 个参数必须是字符串")
        if isinstance(index, bool) or not isinstance(index, int):
            interpreter.raise_runtime_error(token, "charAt 第 2 个参数必须是整数")
        if index < 0 or index >= len(text):
            interpreter.raise_runtime_error(token, "charAt 索引越界")
        return text[index]

    @staticmethod
    def native_substring(
        interpreter: "Interpreter",
        arguments: list[Any],
        token: Token,
    ) -> str:
        """实现 `substring(text, start, end)`：截取字符串片段。"""
        text = arguments[0]
        start = arguments[1]
        end = arguments[2]
        if not isinstance(text, str):
            interpreter.raise_runtime_error(token, "substring 第 1 个参数必须是字符串")
        if isinstance(start, bool) or not isinstance(start, int):
            interpreter.raise_runtime_error(token, "substring 第 2 个参数必须是整数")
        if isinstance(end, bool) or not isinstance(end, int):
            interpreter.raise_runtime_error(token, "substring 第 3 个参数必须是整数")
        if start < 0 or end < start or end > len(text):
            interpreter.raise_runtime_error(token, "substring 范围越界")
        return text[start:end]

    @staticmethod
    def native_is_digit(
        interpreter: "Interpreter",
        arguments: list[Any],
        token: Token,
    ) -> bool:
        """实现 `isDigit(ch)`：判断单字符是否是 0 到 9。"""
        ch = interpreter.require_single_character(arguments[0], token, "isDigit")
        return "0" <= ch <= "9"

    @staticmethod
    def native_is_alpha(
        interpreter: "Interpreter",
        arguments: list[Any],
        token: Token,
    ) -> bool:
        """实现 `isAlpha(ch)`：判断单字符是否是字母或下划线。"""
        ch = interpreter.require_single_character(arguments[0], token, "isAlpha")
        return ("a" <= ch <= "z") or ("A" <= ch <= "Z") or ch == "_"

    @staticmethod
    def native_is_alpha_numeric(
        interpreter: "Interpreter",
        arguments: list[Any],
        token: Token,
    ) -> bool:
        """实现 `isAlphaNumeric(ch)`：判断单字符是否适合组成标识符。"""
        ch = interpreter.require_single_character(arguments[0], token, "isAlphaNumeric")
        return Interpreter.native_is_alpha(
            interpreter,
            [ch],
            token,
        ) or Interpreter.native_is_digit(interpreter, [ch], token)

    @staticmethod
    def native_code_point(
        interpreter: "Interpreter",
        arguments: list[Any],
        token: Token,
    ) -> int:
        """实现 `codePoint(ch)`：返回单字符的 Unicode 编码值。"""
        ch = interpreter.require_single_character(arguments[0], token, "codePoint")
        return ord(ch)

    @staticmethod
    def native_type(
        interpreter: "Interpreter",
        arguments: list[Any],
        token: Token,
    ) -> str:
        """实现 `type(value)`：返回 FR 视角下的运行时类型名称。"""
        value = arguments[0]
        if value is None:
            return "nil"
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, (int, float)):
            return "number"
        if isinstance(value, str):
            return "string"
        if isinstance(value, list):
            return "list"
        if isinstance(value, dict):
            return "map"
        if isinstance(value, (FRFunction, FRNativeFunction)):
            return "function"
        if isinstance(value, Future):
            return "future"
        return "unknown"

    @staticmethod
    def native_str(interpreter: "Interpreter", arguments: list[Any], token: Token) -> str:
        """实现 `str(value)`：复用解释器输出规则转换成字符串。"""
        return interpreter.stringify(arguments[0])

    @staticmethod
    def native_number(
        interpreter: "Interpreter",
        arguments: list[Any],
        token: Token,
    ) -> int | float:
        """实现 `number(value)`：把数字或数字字符串转换成 number。"""
        value = arguments[0]
        if isinstance(value, bool):
            interpreter.raise_runtime_error(token, "number 参数必须是字符串或数字")
        if isinstance(value, (int, float)):
            return value
        if not isinstance(value, str):
            interpreter.raise_runtime_error(token, "number 参数必须是字符串或数字")

        try:
            number = float(value)
        except ValueError:
            interpreter.raise_runtime_error(token, "number 无法转换这个字符串")

        if number.is_integer():
            return int(number)
        return number

    @staticmethod
    def native_has_key(
        interpreter: "Interpreter",
        arguments: list[Any],
        token: Token,
    ) -> bool:
        """实现 `hasKey(map, key)`：判断 Map 是否包含指定 key。"""
        target = arguments[0]
        if not isinstance(target, dict):
            interpreter.raise_runtime_error(token, "hasKey 第 1 个参数必须是 Map")

        normalized_key = interpreter.build_map_key(arguments[1])
        if normalized_key is None:
            interpreter.raise_runtime_error(token, "Map key 类型不支持")
        return normalized_key in target

    @staticmethod
    def native_push(interpreter: "Interpreter", arguments: list[Any], token: Token) -> int:
        """实现 `push(list, value)`：追加元素并返回新的 List 长度。"""
        target = arguments[0]
        if not isinstance(target, list):
            interpreter.raise_runtime_error(token, "push 第 1 个参数必须是 List")
        target.append(arguments[1])
        return len(target)

    @staticmethod
    def native_pop(interpreter: "Interpreter", arguments: list[Any], token: Token) -> Any:
        """实现 `pop(list)`：移除并返回 List 末尾元素。"""
        target = arguments[0]
        if not isinstance(target, list):
            interpreter.raise_runtime_error(token, "pop 参数必须是 List")
        if len(target) == 0:
            interpreter.raise_runtime_error(token, "pop 不能操作空 List")
        return target.pop()

    @staticmethod
    def native_read_file(
        interpreter: "Interpreter",
        arguments: list[Any],
        token: Token,
    ) -> str:
        """实现 `readFile(path)`：读取 base_path 内的 UTF-8 文本。"""
        path = arguments[0]
        if not isinstance(path, str):
            interpreter.raise_runtime_error(token, "readFile 参数必须是字符串")

        target_path = interpreter.resolve_relative_path(token, path, "readFile")

        try:
            return target_path.read_text(encoding="utf-8")
        except OSError as error:
            interpreter.raise_runtime_error(token, f"readFile 读取失败：{error}")

    def resolve_relative_path(self, token: Token, path: str, label: str) -> Path:
        """解析受限制的相对路径。

        `readFile` 和 `import` 都走这里，统一拒绝绝对路径和跳出当前 base_path 的路径。
        """
        requested_path = Path(path)
        if requested_path.is_absolute():
            self.raise_runtime_error(token, f"{label} 只支持相对路径")

        base_path = self.base_path.resolve()
        target_path = (base_path / requested_path).resolve()
        try:
            target_path.relative_to(base_path)
        except ValueError:
            self.raise_runtime_error(token, f"{label} 不能读取工作目录外的文件")
        return target_path

    def require_single_character(self, value: Any, token: Token, name: str) -> str:
        """检查内置函数参数是否为长度为 1 的字符串，并返回该字符。"""
        if not isinstance(value, str) or len(value) != 1:
            self.raise_runtime_error(token, f"{name} 参数必须是单字符字符串")
        return value

    @staticmethod
    def stringify(value: Any) -> str:
        """把运行时值转换成 FR 输出文本。"""
        if value is None:
            return "nil"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, list):
            elements = [Interpreter.stringify(element) for element in value]
            return "[" + ", ".join(elements) + "]"
        if isinstance(value, dict):
            entries = [
                f"{Interpreter.stringify_map_key(key)}: {Interpreter.stringify_map_part(item)}"
                for key, item in value.items()
            ]
            return "{" + ", ".join(entries) + "}"
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)

    @staticmethod
    def stringify_map_part(value: Any) -> str:
        """把 Map 的 key/value 转成更像 FR 字面量的文本。"""
        if isinstance(value, str):
            return f'"{value}"'
        return Interpreter.stringify(value)

    @staticmethod
    def stringify_map_key(value: Any) -> str:
        """把内部 MapKey 还原成用户能理解的 key 文本。"""
        if isinstance(value, MapKey):
            return Interpreter.stringify_map_part(value.value)
        return Interpreter.stringify_map_part(value)

    @staticmethod
    def are_numbers(left: Any, right: Any) -> bool:
        """判断两个值是否都能作为数字运算数。"""
        return isinstance(left, (int, float)) and isinstance(right, (int, float))

    def check_number_operand(self, operator: Token, operand: Any) -> None:
        """检查一元数字运算的操作数类型。"""
        if isinstance(operand, (int, float)):
            return
        self.raise_runtime_error(operator, "操作数必须是数字")

    def check_number_operands(self, operator: Token, left: Any, right: Any) -> None:
        """检查二元数字运算的左右操作数类型。"""
        if self.are_numbers(left, right):
            return
        self.raise_runtime_error(operator, "操作数必须是数字")

    def normalize_list_index(self, operator: Token, index: Any) -> int:
        """把 List 索引规范成整数，并拒绝 bool 和非整数。"""
        if isinstance(index, bool) or not isinstance(index, int):
            self.raise_runtime_error(operator, "列表索引必须是数字")
        return index

    def check_list_index_range(
        self,
        operator: Token,
        target: list[Any],
        index: int,
    ) -> None:
        """检查 List 索引是否在合法范围内。"""
        if index < 0 or index >= len(target):
            self.raise_runtime_error(operator, "列表索引越界")

    def normalize_map_key(self, expression: Expr, key: Any) -> MapKey:
        """把 Map 字面量中的 key 转成内部 MapKey。"""
        normalized_key = self.build_map_key(key)
        if normalized_key is not None:
            return normalized_key
        self.raise_expression_runtime_error(expression, "Map key 类型不支持")

    def normalize_map_key_token(self, operator: Token, key: Any) -> MapKey:
        """把索引表达式中的 Map key 转成内部 MapKey。"""
        normalized_key = self.build_map_key(key)
        if normalized_key is not None:
            return normalized_key
        self.raise_runtime_error(operator, "Map key 类型不支持")

    @staticmethod
    def build_map_key(key: Any) -> MapKey | None:
        """构造内部 MapKey。

        Python 里 `True == 1`，所以这里带上 kind，避免 FR 的 true 和 1 混成同一个 key。
        """
        if isinstance(key, bool):
            return MapKey("bool", key)
        if isinstance(key, str):
            return MapKey("string", key)
        if isinstance(key, (int, float)):
            return MapKey("number", key)
        return None

    def raise_expression_runtime_error(self, expression: Expr, message: str) -> None:
        """根据表达式尽量找出合适的 Token，再抛出运行时错误。"""
        token = self.token_for_expression(expression)
        self.raise_runtime_error(token, message)

    @staticmethod
    def token_for_expression(expression: Expr) -> Token:
        """为表达式选择一个用于报错定位的 Token。"""
        if isinstance(expression, VariableExpr):
            return expression.name
        if isinstance(expression, AssignExpr):
            return expression.name
        if isinstance(expression, IndexExpr):
            return expression.bracket
        if isinstance(expression, IndexAssignExpr):
            return expression.bracket
        if isinstance(expression, AwaitExpr):
            return expression.keyword
        if isinstance(expression, FutureExpr):
            return expression.keyword
        if isinstance(expression, CallExpr):
            return expression.paren
        if isinstance(expression, BinaryExpr):
            return expression.operator
        if isinstance(expression, UnaryExpr):
            return expression.operator
        return Token(TokenType.EOF, "", None, 1, 1)

    @staticmethod
    def raise_runtime_error(operator: Token, message: str) -> None:
        """抛出带行列号的运行时错误。"""
        raise FRRuntimeError(
            f"第 {operator.line} 行，第 {operator.column} 列：{message}"
        )
