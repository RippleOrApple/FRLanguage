"""错误类型。"""


class FRLanguageError(Exception):
    """FRLanguage 错误基类。"""


class LexerError(FRLanguageError):
    """词法错误。"""


class ParserError(FRLanguageError):
    """语法错误。"""


class RuntimeError(FRLanguageError):
    """运行时错误。"""

