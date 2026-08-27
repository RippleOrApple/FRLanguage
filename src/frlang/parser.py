"""语法分析器。"""

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
    PrintStmt,
    Program,
    ReturnStmt,
    Stmt,
    UnaryExpr,
    VarStmt,
    VariableExpr,
    WhileStmt,
)
from .errors import ParserError
from .token import Token, TokenType


class Parser:
    """把 Token 列表解析成 AST。"""

    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.current = 0

    def parse(self) -> Program:
        """解析完整程序。"""
        statements: list[Stmt] = []
        while not self.is_at_end():
            statements.append(self.declaration())
        return Program(statements=statements)

    def declaration(self) -> Stmt:
        if self.match(TokenType.FN):
            return self.function_declaration()
        if self.match(TokenType.LET):
            return self.var_declaration()
        return self.statement()

    def function_declaration(self) -> Stmt:
        name = self.consume(TokenType.IDENTIFIER, "函数声明需要函数名")
        self.consume(TokenType.LEFT_PAREN, "函数名后需要 '('")

        params: list[Token] = []
        if not self.check(TokenType.RIGHT_PAREN):
            while True:
                params.append(
                    self.consume(TokenType.IDENTIFIER, "函数参数需要参数名")
                )
                if not self.match(TokenType.COMMA):
                    break

        self.consume(TokenType.RIGHT_PAREN, "函数参数后需要 ')'")
        self.consume(TokenType.LEFT_BRACE, "函数体前需要 '{'")
        body = self.block()
        return FunctionStmt(name=name, params=params, body=body)

    def var_declaration(self) -> Stmt:
        name = self.consume(TokenType.IDENTIFIER, "变量声明需要变量名")

        initializer: Expr | None = None
        if self.match(TokenType.EQUAL):
            initializer = self.expression()

        self.consume(TokenType.SEMICOLON, "变量声明末尾需要 ';'")
        return VarStmt(name=name, initializer=initializer)

    def statement(self) -> Stmt:
        if self.match(TokenType.PRINT):
            return self.print_statement()
        if self.match(TokenType.RETURN):
            return self.return_statement()
        if self.match(TokenType.IF):
            return self.if_statement()
        if self.match(TokenType.WHILE):
            return self.while_statement()
        if self.match(TokenType.LEFT_BRACE):
            return BlockStmt(self.block())
        return self.expression_statement()

    def if_statement(self) -> Stmt:
        condition = self.expression()
        self.consume(TokenType.LEFT_BRACE, "if 条件后需要 '{'")
        then_branch: Stmt = BlockStmt(self.block())

        else_branch: Stmt | None = None
        if self.match(TokenType.ELSE):
            self.consume(TokenType.LEFT_BRACE, "else 后需要 '{'")
            else_branch = BlockStmt(self.block())

        return IfStmt(
            condition=condition,
            then_branch=then_branch,
            else_branch=else_branch,
        )

    def return_statement(self) -> Stmt:
        keyword = self.previous()
        value: Expr | None = None
        if not self.check(TokenType.SEMICOLON):
            value = self.expression()

        self.consume(TokenType.SEMICOLON, "return 语句末尾需要 ';'")
        return ReturnStmt(keyword=keyword, value=value)

    def while_statement(self) -> Stmt:
        condition = self.expression()
        self.consume(TokenType.LEFT_BRACE, "while 条件后需要 '{'")
        body = BlockStmt(self.block())
        return WhileStmt(condition=condition, body=body)

    def block(self) -> list[Stmt]:
        statements: list[Stmt] = []

        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            statements.append(self.declaration())

        self.consume(TokenType.RIGHT_BRACE, "代码块缺少 '}'")
        return statements

    def print_statement(self) -> Stmt:
        self.consume(TokenType.LEFT_PAREN, "print 后需要 '('")
        expression = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "print 表达式后需要 ')'")
        self.consume(TokenType.SEMICOLON, "print 语句末尾需要 ';'")
        return PrintStmt(expression=expression)

    def expression_statement(self) -> Stmt:
        expression = self.expression()
        self.consume(TokenType.SEMICOLON, "表达式语句末尾需要 ';'")
        return ExprStmt(expression=expression)

    def expression(self) -> Expr:
        return self.assignment()

    def assignment(self) -> Expr:
        expr = self.equality()

        if self.match(TokenType.EQUAL):
            equals = self.previous()
            value = self.assignment()

            if isinstance(expr, VariableExpr):
                return AssignExpr(name=expr.name, value=value)

            if isinstance(expr, IndexExpr):
                return IndexAssignExpr(
                    target=expr.target,
                    bracket=expr.bracket,
                    index=expr.index,
                    value=value,
                )

            raise ParserError(
                f"第 {equals.line} 行，第 {equals.column} 列：无效的赋值目标"
            )

        return expr

    def equality(self) -> Expr:
        expr = self.comparison()

        while self.match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            operator = self.previous()
            right = self.comparison()
            expr = BinaryExpr(left=expr, operator=operator, right=right)

        return expr

    def comparison(self) -> Expr:
        expr = self.term()

        while self.match(
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
        ):
            operator = self.previous()
            right = self.term()
            expr = BinaryExpr(left=expr, operator=operator, right=right)

        return expr

    def term(self) -> Expr:
        expr = self.factor()

        while self.match(TokenType.MINUS, TokenType.PLUS):
            operator = self.previous()
            right = self.factor()
            expr = BinaryExpr(left=expr, operator=operator, right=right)

        return expr

    def factor(self) -> Expr:
        expr = self.unary()

        while self.match(TokenType.SLASH, TokenType.STAR):
            operator = self.previous()
            right = self.unary()
            expr = BinaryExpr(left=expr, operator=operator, right=right)

        return expr

    def unary(self) -> Expr:
        if self.match(TokenType.AWAIT):
            keyword = self.previous()
            expression = self.unary()
            return AwaitExpr(keyword=keyword, expression=expression)

        if self.match(TokenType.BANG, TokenType.MINUS):
            operator = self.previous()
            right = self.unary()
            return UnaryExpr(operator=operator, right=right)

        return self.call()

    def call(self) -> Expr:
        expr = self.primary()

        while True:
            if self.match(TokenType.LEFT_PAREN):
                expr = self.finish_call(expr)
            elif self.match(TokenType.LEFT_BRACKET):
                expr = self.finish_index(expr)
            else:
                break

        return expr

    def finish_call(self, callee: Expr) -> Expr:
        arguments: list[Expr] = []
        if not self.check(TokenType.RIGHT_PAREN):
            while True:
                arguments.append(self.expression())
                if not self.match(TokenType.COMMA):
                    break

        paren = self.consume(TokenType.RIGHT_PAREN, "函数调用参数后需要 ')'")
        return CallExpr(callee=callee, paren=paren, arguments=arguments)

    def finish_index(self, target: Expr) -> Expr:
        bracket = self.previous()
        index = self.expression()
        self.consume(TokenType.RIGHT_BRACKET, "索引表达式缺少 ']'")
        return IndexExpr(target=target, bracket=bracket, index=index)

    def primary(self) -> Expr:
        if self.match(TokenType.FALSE):
            return LiteralExpr(False)
        if self.match(TokenType.TRUE):
            return LiteralExpr(True)
        if self.match(TokenType.NUMBER, TokenType.STRING):
            return LiteralExpr(self.previous().literal)
        if self.match(TokenType.IDENTIFIER):
            return VariableExpr(self.previous())
        if self.match(TokenType.FUTURE):
            keyword = self.previous()
            self.consume(TokenType.LEFT_BRACE, "future 后需要 '{'")
            return FutureExpr(keyword=keyword, body=self.block())
        if self.match(TokenType.LEFT_BRACKET):
            return self.list_literal()
        if self.match(TokenType.LEFT_PAREN):
            expr = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "括号表达式缺少 ')'")
            return GroupingExpr(expr)

        token = self.peek()
        raise ParserError(
            f"第 {token.line} 行，第 {token.column} 列：需要表达式"
        )

    def list_literal(self) -> Expr:
        elements: list[Expr] = []
        if not self.check(TokenType.RIGHT_BRACKET):
            while True:
                elements.append(self.expression())
                if not self.match(TokenType.COMMA):
                    break

        self.consume(TokenType.RIGHT_BRACKET, "列表字面量缺少 ']'")
        return ListExpr(elements)

    def match(self, *types: TokenType) -> bool:
        for token_type in types:
            if self.check(token_type):
                self.advance()
                return True
        return False

    def consume(self, token_type: TokenType, message: str) -> Token:
        if self.check(token_type):
            return self.advance()

        token = self.peek()
        raise ParserError(f"第 {token.line} 行，第 {token.column} 列：{message}")

    def check(self, token_type: TokenType) -> bool:
        if self.is_at_end():
            return token_type is TokenType.EOF
        return self.peek().type is token_type

    def advance(self) -> Token:
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def is_at_end(self) -> bool:
        return self.peek().type is TokenType.EOF

    def peek(self) -> Token:
        return self.tokens[self.current]

    def previous(self) -> Token:
        return self.tokens[self.current - 1]
