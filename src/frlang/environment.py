"""变量环境。"""

from typing import Any

from .errors import RuntimeError as FRRuntimeError
from .token import Token


class Environment:
    """保存变量，并支持嵌套作用域。"""

    def __init__(self, enclosing: "Environment | None" = None) -> None:
        self.enclosing = enclosing
        self.values: dict[str, Any] = {}

    def define(self, name: str, value: Any) -> None:
        """在当前环境中定义变量。"""
        self.values[name] = value

    def get(self, name: Token) -> Any:
        """读取变量值。"""
        if name.lexeme in self.values:
            return self.values[name.lexeme]

        if self.enclosing is not None:
            return self.enclosing.get(name)

        raise FRRuntimeError(
            f"第 {name.line} 行，第 {name.column} 列：变量 {name.lexeme} 未定义"
        )

    def assign(self, name: Token, value: Any) -> None:
        """给已经存在的变量赋值。"""
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
            return

        if self.enclosing is not None:
            self.enclosing.assign(name, value)
            return

        raise FRRuntimeError(
            f"第 {name.line} 行，第 {name.column} 列：变量 {name.lexeme} 未定义"
        )
