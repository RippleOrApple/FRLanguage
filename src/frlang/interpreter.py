"""解释器核心。"""

from dataclasses import dataclass
from typing import Any

from .ast import (
    AssignExpr,
    AwaitExpr,
    BinaryExpr,
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
from .environment import Environment
from .errors import RuntimeError as FRRuntimeError
from .future import Future, FutureState
from .runtime import Runtime
from .token import Token, TokenType


class ReturnSignal(Exception):
    """函数 return 使用的内部控制流信号。"""

    def __init__(self, value: Any) -> None:
        self.value = value


@dataclass(frozen=True)
class MapKey:
    """Map 运行时使用的内部 key，避免 true 和 1 在 Python dict 中混淆。"""

    kind: str
    value: Any


class FRFunction:
    """FRLanguage 函数对象。"""

    def __init__(self, declaration: FunctionStmt, closure: Environment) -> None:
        self.declaration = declaration
        self.closure = closure

    def call(self, interpreter: "Interpreter", arguments: list[Any]) -> Any:
        environment = Environment(self.closure)
        for param, argument in zip(self.declaration.params, arguments):
            environment.define(param.lexeme, argument)

        try:
            interpreter.execute_block(self.declaration.body, environment)
        except ReturnSignal as signal:
            return signal.value

        return None

    def arity(self) -> int:
        return len(self.declaration.params)

    def __str__(self) -> str:
        return f"<fn {self.declaration.name.lexeme}>"


class Interpreter:
    """执行 FRLanguage AST。"""

    def __init__(self) -> None:
        self.globals = Environment()
        self.environment = self.globals
        self.runtime = Runtime()
        self.output: list[str] = []

    def interpret(self, program: Program) -> None:
        """执行程序。"""
        for statement in program.statements:
            self.execute(statement)

    def execute(self, statement: Stmt) -> None:
        if isinstance(statement, VarStmt):
            value = None
            if statement.initializer is not None:
                value = self.evaluate(statement.initializer)
            self.environment.define(statement.name.lexeme, value)
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
                self.execute(statement.body)
            return

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
        previous = self.environment
        try:
            self.environment = environment
            for statement in statements:
                self.execute(statement)
        finally:
            self.environment = previous

    def evaluate(self, expression: Expr) -> Any:
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

            if not isinstance(callee, FRFunction):
                self.raise_runtime_error(expression.paren, "只能调用函数")

            if len(arguments) != callee.arity():
                self.raise_runtime_error(
                    expression.paren,
                    f"参数数量不匹配：需要 {callee.arity()} 个，实际 {len(arguments)} 个",
                )

            return callee.call(self, arguments)

        if isinstance(expression, FutureExpr):
            future = Future()
            closure = self.environment

            def run_future_block() -> None:
                try:
                    self.execute_block(expression.body, Environment(closure))
                except ReturnSignal as signal:
                    future.resolve(signal.value)
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
            right = self.evaluate(expression.right)
            operator_type = expression.operator.type

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
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        return True

    @staticmethod
    def stringify(value: Any) -> str:
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
        if isinstance(value, str):
            return f'"{value}"'
        return Interpreter.stringify(value)

    @staticmethod
    def stringify_map_key(value: Any) -> str:
        if isinstance(value, MapKey):
            return Interpreter.stringify_map_part(value.value)
        return Interpreter.stringify_map_part(value)

    @staticmethod
    def are_numbers(left: Any, right: Any) -> bool:
        return isinstance(left, (int, float)) and isinstance(right, (int, float))

    def check_number_operand(self, operator: Token, operand: Any) -> None:
        if isinstance(operand, (int, float)):
            return
        self.raise_runtime_error(operator, "操作数必须是数字")

    def check_number_operands(self, operator: Token, left: Any, right: Any) -> None:
        if self.are_numbers(left, right):
            return
        self.raise_runtime_error(operator, "操作数必须是数字")

    def normalize_list_index(self, operator: Token, index: Any) -> int:
        if isinstance(index, bool) or not isinstance(index, int):
            self.raise_runtime_error(operator, "列表索引必须是数字")
        return index

    def check_list_index_range(
        self,
        operator: Token,
        target: list[Any],
        index: int,
    ) -> None:
        if index < 0 or index >= len(target):
            self.raise_runtime_error(operator, "列表索引越界")

    def normalize_map_key(self, expression: Expr, key: Any) -> MapKey:
        normalized_key = self.build_map_key(key)
        if normalized_key is not None:
            return normalized_key
        self.raise_expression_runtime_error(expression, "Map key 类型不支持")

    def normalize_map_key_token(self, operator: Token, key: Any) -> MapKey:
        normalized_key = self.build_map_key(key)
        if normalized_key is not None:
            return normalized_key
        self.raise_runtime_error(operator, "Map key 类型不支持")

    @staticmethod
    def build_map_key(key: Any) -> MapKey | None:
        if isinstance(key, bool):
            return MapKey("bool", key)
        if isinstance(key, str):
            return MapKey("string", key)
        if isinstance(key, (int, float)):
            return MapKey("number", key)
        return None

    def raise_expression_runtime_error(self, expression: Expr, message: str) -> None:
        token = self.token_for_expression(expression)
        self.raise_runtime_error(token, message)

    @staticmethod
    def token_for_expression(expression: Expr) -> Token:
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
        raise FRRuntimeError(
            f"第 {operator.line} 行，第 {operator.column} 列：{message}"
        )
