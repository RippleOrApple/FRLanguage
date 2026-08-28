"""Token 定义。"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class TokenType(Enum):
    """FRLanguage 的 Token 类型。"""

    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    LEFT_BRACKET = auto()
    RIGHT_BRACKET = auto()
    COMMA = auto()
    COLON = auto()
    DOT = auto()
    MINUS = auto()
    PLUS = auto()
    SEMICOLON = auto()
    SLASH = auto()
    STAR = auto()

    BANG = auto()
    BANG_EQUAL = auto()
    EQUAL = auto()
    EQUAL_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()

    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()

    LET = auto()
    IMPORT = auto()
    FN = auto()
    RETURN = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    BREAK = auto()
    AND = auto()
    OR = auto()
    TRUE = auto()
    FALSE = auto()
    NIL = auto()
    FUTURE = auto()
    AWAIT = auto()
    PRINT = auto()

    EOF = auto()


@dataclass(frozen=True)
class Token:
    """词法分析阶段产出的最小单元。"""

    type: TokenType
    lexeme: str
    literal: Any
    line: int
    column: int
