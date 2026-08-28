"""命令行入口。"""

import sys
from pathlib import Path

from .errors import FRLanguageError
from .interpreter import Interpreter
from .lexer import Lexer
from .parser import Parser


def run_source(source: str, base_path: Path | str | None = None) -> list[str]:
    """运行源码并返回输出行。

    `base_path` 会传给解释器，用作 `readFile` 和 `import` 的相对路径起点。
    """
    tokens = Lexer(source).scan_tokens()
    program = Parser(tokens).parse()
    interpreter = Interpreter(base_path=base_path)
    interpreter.interpret(program)
    return interpreter.output


def main(argv: list[str] | None = None) -> None:
    """运行 FRLanguage 命令行程序。

    命令行只接收一个 `.fr` 文件路径，读取源码后交给 `run_source` 执行。
    """
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("用法：frlang <文件路径>", file=sys.stderr)
        raise SystemExit(64)

    try:
        source_path = Path(args[0])
        source = source_path.read_text(encoding="utf-8")
    except OSError as error:
        print(f"文件读取失败：{args[0]}", file=sys.stderr)
        print(str(error), file=sys.stderr)
        raise SystemExit(66) from None

    try:
        output = run_source(source, base_path=source_path.parent)
    except FRLanguageError as error:
        print(f"错误：{error}", file=sys.stderr)
        raise SystemExit(70) from None

    for line in output:
        print(line)


if __name__ == "__main__":
    main()
