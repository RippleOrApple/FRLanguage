"""命令行入口。"""

import sys
from pathlib import Path

from .errors import FRLanguageError
from .interpreter import Interpreter
from .lexer import Lexer
from .parser import Parser


def run_source(source: str) -> list[str]:
    """运行源码并返回输出行。"""
    tokens = Lexer(source).scan_tokens()
    program = Parser(tokens).parse()
    interpreter = Interpreter()
    interpreter.interpret(program)
    return interpreter.output


def main(argv: list[str] | None = None) -> None:
    """运行 FRLanguage 命令行程序。"""
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("用法：frlang <文件路径>", file=sys.stderr)
        raise SystemExit(64)

    try:
        source = Path(args[0]).read_text(encoding="utf-8")
    except OSError as error:
        print(f"文件读取失败：{args[0]}", file=sys.stderr)
        print(str(error), file=sys.stderr)
        raise SystemExit(66) from None

    try:
        output = run_source(source)
    except FRLanguageError as error:
        print(f"错误：{error}", file=sys.stderr)
        raise SystemExit(70) from None

    for line in output:
        print(line)


if __name__ == "__main__":
    main()
