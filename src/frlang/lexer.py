"""词法分析器。"""

from typing import Any

from .errors import LexerError
from .token import Token, TokenType


KEYWORDS: dict[str, TokenType] = {
    "let": TokenType.LET,
    "fn": TokenType.FN,
    "return": TokenType.RETURN,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "future": TokenType.FUTURE,
    "await": TokenType.AWAIT,
    "print": TokenType.PRINT,
}


class Lexer:
    """把源码字符串转换为 Token 列表。"""

    def __init__(self, source: str) -> None:
        self.source = source
        self.tokens: list[Token] = []
        self.start = 0
        self.current = 0
        self.line = 1
        self.column = 1
        self.start_line = 1
        self.start_column = 1

    def scan_tokens(self) -> list[Token]:
        """扫描源码并返回 Token 列表。"""
        while not self.is_at_end():
            self.start = self.current
            self.start_line = self.line
            self.start_column = self.column
            self.scan_token()

        self.tokens.append(Token(TokenType.EOF, "", None, self.line, self.column))
        return self.tokens

    def scan_token(self) -> None:
        char = self.advance()

        match char:
            case "(":
                self.add_token(TokenType.LEFT_PAREN)
            case ")":
                self.add_token(TokenType.RIGHT_PAREN)
            case "{":
                self.add_token(TokenType.LEFT_BRACE)
            case "}":
                self.add_token(TokenType.RIGHT_BRACE)
            case ",":
                self.add_token(TokenType.COMMA)
            case ".":
                self.add_token(TokenType.DOT)
            case "-":
                self.add_token(TokenType.MINUS)
            case "+":
                self.add_token(TokenType.PLUS)
            case ";":
                self.add_token(TokenType.SEMICOLON)
            case "*":
                self.add_token(TokenType.STAR)
            case "!":
                self.add_token(TokenType.BANG_EQUAL if self.match("=") else TokenType.BANG)
            case "=":
                self.add_token(TokenType.EQUAL_EQUAL if self.match("=") else TokenType.EQUAL)
            case "<":
                self.add_token(TokenType.LESS_EQUAL if self.match("=") else TokenType.LESS)
            case ">":
                self.add_token(TokenType.GREATER_EQUAL if self.match("=") else TokenType.GREATER)
            case "/":
                if self.match("/"):
                    self.skip_line_comment()
                else:
                    self.add_token(TokenType.SLASH)
            case " " | "\r" | "\t":
                pass
            case "\n":
                pass
            case '"':
                self.string()
            case _:
                if char.isdigit():
                    self.number()
                elif self.is_identifier_start(char):
                    self.identifier()
                else:
                    self.raise_error(f"无法识别的字符：{char}")

    def identifier(self) -> None:
        while self.is_identifier_part(self.peek()):
            self.advance()

        text = self.source[self.start : self.current]
        token_type = KEYWORDS.get(text, TokenType.IDENTIFIER)
        literal = self.keyword_literal(token_type)
        self.add_token(token_type, literal)

    def number(self) -> None:
        while self.peek().isdigit():
            self.advance()

        if self.peek() == "." and self.peek_next().isdigit():
            self.advance()
            while self.peek().isdigit():
                self.advance()

        text = self.source[self.start : self.current]
        literal: int | float
        if "." in text:
            literal = float(text)
        else:
            literal = int(text)
        self.add_token(TokenType.NUMBER, literal)

    def string(self) -> None:
        while self.peek() != '"' and not self.is_at_end():
            self.advance()

        if self.is_at_end():
            self.raise_error("字符串没有结束")

        self.advance()
        literal = self.source[self.start + 1 : self.current - 1]
        self.add_token(TokenType.STRING, literal)

    def skip_line_comment(self) -> None:
        while self.peek() != "\n" and not self.is_at_end():
            self.advance()

    def add_token(self, token_type: TokenType, literal: Any = None) -> None:
        text = self.source[self.start : self.current]
        self.tokens.append(
            Token(token_type, text, literal, self.start_line, self.start_column)
        )

    def advance(self) -> str:
        char = self.source[self.current]
        self.current += 1
        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def match(self, expected: str) -> bool:
        if self.is_at_end() or self.source[self.current] != expected:
            return False

        self.advance()
        return True

    def peek(self) -> str:
        if self.is_at_end():
            return "\0"
        return self.source[self.current]

    def peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return "\0"
        return self.source[self.current + 1]

    def is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def raise_error(self, message: str) -> None:
        raise LexerError(
            f"第 {self.start_line} 行，第 {self.start_column} 列：{message}"
        )

    @staticmethod
    def keyword_literal(token_type: TokenType) -> Any:
        if token_type is TokenType.TRUE:
            return True
        if token_type is TokenType.FALSE:
            return False
        return None

    @staticmethod
    def is_identifier_start(char: str) -> bool:
        return char.isalpha() or char == "_"

    @staticmethod
    def is_identifier_part(char: str) -> bool:
        return char.isalnum() or char == "_"
