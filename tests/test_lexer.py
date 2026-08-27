import unittest

from frlang.errors import LexerError
from frlang.lexer import Lexer
from frlang.token import TokenType


class LexerTest(unittest.TestCase):
    def token_types(self, source: str) -> list[TokenType]:
        return [token.type for token in Lexer(source).scan_tokens()]

    def test_empty_source_returns_eof(self) -> None:
        tokens = Lexer("").scan_tokens()

        self.assertIs(tokens[-1].type, TokenType.EOF)

    def test_scans_keywords_identifiers_and_punctuation(self) -> None:
        source = """
        fn main() {
          let value = future {
            return await work();
          };
        }
        """

        self.assertEqual(
            self.token_types(source),
            [
                TokenType.FN,
                TokenType.IDENTIFIER,
                TokenType.LEFT_PAREN,
                TokenType.RIGHT_PAREN,
                TokenType.LEFT_BRACE,
                TokenType.LET,
                TokenType.IDENTIFIER,
                TokenType.EQUAL,
                TokenType.FUTURE,
                TokenType.LEFT_BRACE,
                TokenType.RETURN,
                TokenType.AWAIT,
                TokenType.IDENTIFIER,
                TokenType.LEFT_PAREN,
                TokenType.RIGHT_PAREN,
                TokenType.SEMICOLON,
                TokenType.RIGHT_BRACE,
                TokenType.SEMICOLON,
                TokenType.RIGHT_BRACE,
                TokenType.EOF,
            ],
        )

    def test_scans_literals_and_operators(self) -> None:
        source = 'let ok = "hi"; let n = 12.5 * 2 >= 20 == true;'
        tokens = Lexer(source).scan_tokens()

        self.assertEqual(
            [token.type for token in tokens],
            [
                TokenType.LET,
                TokenType.IDENTIFIER,
                TokenType.EQUAL,
                TokenType.STRING,
                TokenType.SEMICOLON,
                TokenType.LET,
                TokenType.IDENTIFIER,
                TokenType.EQUAL,
                TokenType.NUMBER,
                TokenType.STAR,
                TokenType.NUMBER,
                TokenType.GREATER_EQUAL,
                TokenType.NUMBER,
                TokenType.EQUAL_EQUAL,
                TokenType.TRUE,
                TokenType.SEMICOLON,
                TokenType.EOF,
            ],
        )
        self.assertEqual(tokens[3].literal, "hi")
        self.assertEqual(tokens[8].literal, 12.5)
        self.assertEqual(tokens[10].literal, 2)

    def test_ignores_line_comments(self) -> None:
        tokens = self.token_types("let x = 1; // ignore this\nprint(x);")

        self.assertEqual(
            tokens,
            [
                TokenType.LET,
                TokenType.IDENTIFIER,
                TokenType.EQUAL,
                TokenType.NUMBER,
                TokenType.SEMICOLON,
                TokenType.PRINT,
                TokenType.LEFT_PAREN,
                TokenType.IDENTIFIER,
                TokenType.RIGHT_PAREN,
                TokenType.SEMICOLON,
                TokenType.EOF,
            ],
        )

    def test_records_line_and_column(self) -> None:
        tokens = Lexer("let x = 1;\n  print(x);").scan_tokens()
        print_token = tokens[5]

        self.assertIs(print_token.type, TokenType.PRINT)
        self.assertEqual(print_token.line, 2)
        self.assertEqual(print_token.column, 3)

    def test_unterminated_string_raises_lexer_error(self) -> None:
        with self.assertRaisesRegex(LexerError, "字符串没有结束"):
            Lexer('"oops').scan_tokens()


if __name__ == "__main__":
    unittest.main()
