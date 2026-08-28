import unittest

from frlang.ast import (
    BinaryExpr,
    ExprStmt,
    GroupingExpr,
    LiteralExpr,
    PrintStmt,
    Program,
    VarStmt,
    VariableExpr,
)
from frlang.lexer import Lexer
from frlang.parser import Parser
from frlang.token import Token, TokenType


class ParserTest(unittest.TestCase):
    def parse_source(self, source: str) -> Program:
        """把源码走完 Lexer 和 Parser，返回解析后的 Program。"""
        return Parser(Lexer(source).scan_tokens()).parse()

    def test_empty_tokens_parse_to_empty_program(self) -> None:
        program = Parser([Token(TokenType.EOF, "", None, 1, 1)]).parse()

        self.assertIsInstance(program, Program)
        self.assertEqual(program.statements, [])

    def test_parses_variable_declaration(self) -> None:
        program = self.parse_source("let answer = 42;")

        self.assertEqual(
            program,
            Program(
                statements=[
                    VarStmt(
                        name=Token(TokenType.IDENTIFIER, "answer", None, 1, 5),
                        initializer=LiteralExpr(42),
                    )
                ]
            ),
        )

    def test_parses_print_statement(self) -> None:
        program = self.parse_source('print("hello");')

        self.assertEqual(
            program,
            Program(statements=[PrintStmt(expression=LiteralExpr("hello"))]),
        )

    def test_parses_nil_literal(self) -> None:
        """验证 nil 会被解析成值为 None 的字面量表达式。"""
        program = self.parse_source("print(nil);")

        self.assertEqual(
            program,
            Program(statements=[PrintStmt(expression=LiteralExpr(None))]),
        )

    def test_parses_expression_precedence(self) -> None:
        program = self.parse_source("print(1 + 2 * 3);")

        self.assertEqual(
            program.statements[0],
            PrintStmt(
                expression=BinaryExpr(
                    left=LiteralExpr(1),
                    operator=Token(TokenType.PLUS, "+", None, 1, 9),
                    right=BinaryExpr(
                        left=LiteralExpr(2),
                        operator=Token(TokenType.STAR, "*", None, 1, 13),
                        right=LiteralExpr(3),
                    ),
                )
            ),
        )

    def test_parses_grouping_expression(self) -> None:
        program = self.parse_source("print((1 + 2) * 3);")

        self.assertEqual(
            program.statements[0],
            PrintStmt(
                expression=BinaryExpr(
                    left=GroupingExpr(
                        expression=BinaryExpr(
                            left=LiteralExpr(1),
                            operator=Token(TokenType.PLUS, "+", None, 1, 10),
                            right=LiteralExpr(2),
                        )
                    ),
                    operator=Token(TokenType.STAR, "*", None, 1, 15),
                    right=LiteralExpr(3),
                )
            ),
        )

    def test_parses_variable_expression_statement(self) -> None:
        program = self.parse_source("answer;")

        self.assertEqual(
            program,
            Program(
                statements=[
                    ExprStmt(
                        expression=VariableExpr(
                            name=Token(TokenType.IDENTIFIER, "answer", None, 1, 1)
                        )
                    )
                ]
            ),
        )


if __name__ == "__main__":
    unittest.main()
