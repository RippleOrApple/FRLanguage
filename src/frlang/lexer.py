"""词法分析器。"""

from typing import Any

from .errors import LexerError
from .token import Token, TokenType


KEYWORDS: dict[str, TokenType] = {
    "let": TokenType.LET,
    "import": TokenType.IMPORT,
    "fn": TokenType.FN,
    "return": TokenType.RETURN,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "break": TokenType.BREAK,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "future": TokenType.FUTURE,
    "await": TokenType.AWAIT,
    "print": TokenType.PRINT,
}


class Lexer:
    """把源码字符串转换为 Token 列表。"""

    def __init__(self, source: str) -> None:
        """初始化扫描状态。

        `start` 指向当前 Token 的起点，`current` 指向下一个将被读取的字符。
        行列信息分成当前位置和 Token 起始位置，方便错误信息定位到词素开头。
        """
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
        """扫描一个 Token。

        这个函数只看当前字符以及必要的下一个字符，不理解语法结构。
        例如 `!=` 会在这里变成一个 Token，但 `a != b` 的表达式关系由 Parser 处理。
        """
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
            case "[":
                self.add_token(TokenType.LEFT_BRACKET)
            case "]":
                self.add_token(TokenType.RIGHT_BRACKET)
            case ",":
                self.add_token(TokenType.COMMA)
            case ":":
                self.add_token(TokenType.COLON)
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
        """扫描标识符或关键字。

        标识符会一直读到不是字母、数字或下划线的位置。
        扫描结束后再查 `KEYWORDS`，决定它是普通变量名还是语言关键字。
        """
        while self.is_identifier_part(self.peek()):
            self.advance()

        text = self.source[self.start : self.current]
        token_type = KEYWORDS.get(text, TokenType.IDENTIFIER)
        literal = self.keyword_literal(token_type)
        self.add_token(token_type, literal)

    def number(self) -> None:
        """扫描整数或小数数字字面量。

        数字在遇到非数字字符时结束；如果遇到 `.` 且后面还是数字，就继续读取小数部分。
        """
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
        """扫描双引号字符串字面量。

        字符串会把支持的转义序列转换进 literal，未闭合或未知转义都会抛出词法错误。
        """
        literal_chars: list[str] = []
        while self.peek() != '"' and not self.is_at_end():
            if self.peek() == "\\":
                self.advance()
                if self.is_at_end():
                    self.raise_error("字符串没有结束")

                escaped = self.advance()
                literal = self.string_escape_value(escaped)
                if literal is None:
                    self.raise_error(f"未知字符串转义：\\{escaped}")
                literal_chars.append(literal)
            else:
                literal_chars.append(self.advance())

        if self.is_at_end():
            self.raise_error("字符串没有结束")

        self.advance()
        literal = "".join(literal_chars)
        self.add_token(TokenType.STRING, literal)

    def skip_line_comment(self) -> None:
        """跳过 `//` 单行注释。

        注释内容不会生成 Token，扫描会停在换行符或源码末尾。
        """
        while self.peek() != "\n" and not self.is_at_end():
            self.advance()

    def add_token(self, token_type: TokenType, literal: Any = None) -> None:
        """把当前词素保存成 Token。

        `lexeme` 保留源码原文，`literal` 保存已经转换好的运行时值，例如数字和字符串内容。
        """
        text = self.source[self.start : self.current]
        self.tokens.append(
            Token(token_type, text, literal, self.start_line, self.start_column)
        )

    def advance(self) -> str:
        """读取当前字符并前进一个位置。

        所有真正消耗字符的地方都走这里，这样行号和列号可以集中维护。
        """
        char = self.source[self.current]
        self.current += 1
        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def match(self, expected: str) -> bool:
        """如果下一个字符是期望字符，就消费它并返回 True。

        主要用于识别两个字符的运算符，例如 `!=`、`==`、`<=`、`>=` 和 `//`。
        """
        if self.is_at_end() or self.source[self.current] != expected:
            return False

        self.advance()
        return True

    def peek(self) -> str:
        """查看当前字符但不消费它。"""
        if self.is_at_end():
            return "\0"
        return self.source[self.current]

    def peek_next(self) -> str:
        """查看当前字符后面的一个字符但不消费它。"""
        if self.current + 1 >= len(self.source):
            return "\0"
        return self.source[self.current + 1]

    def is_at_end(self) -> bool:
        """判断扫描游标是否已经到达源码末尾。"""
        return self.current >= len(self.source)

    def raise_error(self, message: str) -> None:
        """抛出带行列号的词法错误。"""
        raise LexerError(
            f"第 {self.start_line} 行，第 {self.start_column} 列：{message}"
        )

    @staticmethod
    def keyword_literal(token_type: TokenType) -> Any:
        """返回关键字自带的字面量值。

        目前只有 `true` 和 `false` 在词法阶段就能转换成布尔值，其他关键字没有 literal。
        """
        if token_type is TokenType.TRUE:
            return True
        if token_type is TokenType.FALSE:
            return False
        return None

    @staticmethod
    def string_escape_value(char: str) -> str | None:
        """把字符串转义字符转换成真实字符，不支持时返回 None。"""
        escapes = {
            '"': '"',
            "\\": "\\",
            "n": "\n",
            "t": "\t",
            "r": "\r",
        }
        return escapes.get(char)

    @staticmethod
    def is_identifier_start(char: str) -> bool:
        """判断字符是否能作为标识符开头。"""
        return char.isalpha() or char == "_"

    @staticmethod
    def is_identifier_part(char: str) -> bool:
        """判断字符是否能作为标识符后续部分。"""
        return char.isalnum() or char == "_"
