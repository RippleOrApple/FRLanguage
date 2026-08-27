"""语法分析器。"""

from .ast import (
    AssignExpr,
    AwaitExpr,
    BinaryExpr,
    BlockStmt,
    BreakStmt,
    CallExpr,
    Expr,
    ExprStmt,
    FunctionStmt,
    FutureExpr,
    GroupingExpr,
    IfStmt,
    ImportStmt,
    IndexAssignExpr,
    IndexExpr,
    ListExpr,
    LiteralExpr,
    MapEntry,
    MapExpr,
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
        """初始化 Parser 游标。

        `current` 指向下一个将被消费的 Token，Parser 会从左到右递归下降解析。
        """
        self.tokens = tokens
        self.current = 0

    def parse(self) -> Program:
        """解析完整程序。"""
        statements: list[Stmt] = []
        while not self.is_at_end():
            statements.append(self.declaration())
        return Program(statements=statements)

    def declaration(self) -> Stmt:
        """解析声明级语法。

        声明会向当前作用域引入名字或文件内容，例如 `let`、`fn`、`import`。
        如果当前 Token 不是声明开头，就交给普通语句解析。
        """
        if self.match(TokenType.IMPORT):
            return self.import_statement()
        if self.match(TokenType.FN):
            return self.function_declaration()
        if self.match(TokenType.LET):
            return self.var_declaration()
        return self.statement()

    def import_statement(self) -> Stmt:
        """解析 `import "file.fr";` 语句。"""
        keyword = self.previous()
        path = self.consume(TokenType.STRING, "import 后需要字符串路径")
        self.consume(TokenType.SEMICOLON, "import 语句末尾需要 ';'")
        return ImportStmt(keyword=keyword, path=path)

    def function_declaration(self) -> Stmt:
        """解析函数声明。

        函数声明会记录函数名、参数 Token 列表和函数体语句列表，真正绑定函数对象发生在解释阶段。
        """
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
        """解析变量声明。

        `let name;` 的 initializer 为 None，解释器会把它初始化成 nil。
        """
        name = self.consume(TokenType.IDENTIFIER, "变量声明需要变量名")

        initializer: Expr | None = None
        if self.match(TokenType.EQUAL):
            initializer = self.expression()

        self.consume(TokenType.SEMICOLON, "变量声明末尾需要 ';'")
        return VarStmt(name=name, initializer=initializer)

    def statement(self) -> Stmt:
        """解析普通语句。

        语句通常表示控制流或副作用；如果都匹配不上，就按表达式语句处理。
        """
        if self.match(TokenType.PRINT):
            return self.print_statement()
        if self.match(TokenType.RETURN):
            return self.return_statement()
        if self.match(TokenType.BREAK):
            return self.break_statement()
        if self.match(TokenType.IF):
            return self.if_statement()
        if self.match(TokenType.WHILE):
            return self.while_statement()
        if self.match(TokenType.LEFT_BRACE):
            return BlockStmt(self.block())
        return self.expression_statement()

    def if_statement(self) -> Stmt:
        """解析 if/else 条件分支。"""
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
        """解析 return 语句。

        return 后可以没有表达式，此时解释器会返回 nil。
        """
        keyword = self.previous()
        value: Expr | None = None
        if not self.check(TokenType.SEMICOLON):
            value = self.expression()

        self.consume(TokenType.SEMICOLON, "return 语句末尾需要 ';'")
        return ReturnStmt(keyword=keyword, value=value)

    def break_statement(self) -> Stmt:
        """解析 break 语句。

        Parser 只负责识别语法；break 是否在 while 中使用由解释器在运行时检查。
        """
        keyword = self.previous()
        self.consume(TokenType.SEMICOLON, "break 语句末尾需要 ';'")
        return BreakStmt(keyword=keyword)

    def while_statement(self) -> Stmt:
        """解析 while 循环。

        while 条件是表达式，循环体统一包装成 BlockStmt，方便解释器按语句执行。
        """
        condition = self.expression()
        self.consume(TokenType.LEFT_BRACE, "while 条件后需要 '{'")
        body = BlockStmt(self.block())
        return WhileStmt(condition=condition, body=body)

    def block(self) -> list[Stmt]:
        """解析 `{ ... }` 中的语句列表。

        调用方已经消费了左大括号，本函数负责读到匹配的右大括号。
        """
        statements: list[Stmt] = []

        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            statements.append(self.declaration())

        self.consume(TokenType.RIGHT_BRACE, "代码块缺少 '}'")
        return statements

    def print_statement(self) -> Stmt:
        """解析 print 特殊语句。

        第一版把 print 当成语句而不是普通函数，所以它有自己的解析入口。
        """
        self.consume(TokenType.LEFT_PAREN, "print 后需要 '('")
        expression = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "print 表达式后需要 ')'")
        self.consume(TokenType.SEMICOLON, "print 语句末尾需要 ';'")
        return PrintStmt(expression=expression)

    def expression_statement(self) -> Stmt:
        """解析表达式语句。

        表达式语句会执行表达式但不自动输出结果，适合函数调用或赋值。
        """
        expression = self.expression()
        self.consume(TokenType.SEMICOLON, "表达式语句末尾需要 ';'")
        return ExprStmt(expression=expression)

    def expression(self) -> Expr:
        """解析表达式入口。"""
        return self.assignment()

    def assignment(self) -> Expr:
        """解析赋值表达式。

        赋值是右结合的，所以右侧再次调用 `assignment()`。
        只有变量读取和索引读取可以作为赋值目标。
        """
        expr = self.or_()

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

    def or_(self) -> Expr:
        """解析 `or` 逻辑表达式。

        `or` 的优先级低于 `and`，解释阶段会短路求值。
        """
        expr = self.and_()

        while self.match(TokenType.OR):
            operator = self.previous()
            right = self.and_()
            expr = BinaryExpr(left=expr, operator=operator, right=right)

        return expr

    def and_(self) -> Expr:
        """解析 `and` 逻辑表达式。

        `and` 的优先级低于比较和相等运算，解释阶段会短路求值。
        """
        expr = self.equality()

        while self.match(TokenType.AND):
            operator = self.previous()
            right = self.equality()
            expr = BinaryExpr(left=expr, operator=operator, right=right)

        return expr

    def equality(self) -> Expr:
        """解析 `==` 和 `!=`。"""
        expr = self.comparison()

        while self.match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            operator = self.previous()
            right = self.comparison()
            expr = BinaryExpr(left=expr, operator=operator, right=right)

        return expr

    def comparison(self) -> Expr:
        """解析大小比较运算。"""
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
        """解析加减法。"""
        expr = self.factor()

        while self.match(TokenType.MINUS, TokenType.PLUS):
            operator = self.previous()
            right = self.factor()
            expr = BinaryExpr(left=expr, operator=operator, right=right)

        return expr

    def factor(self) -> Expr:
        """解析乘除法。"""
        expr = self.unary()

        while self.match(TokenType.SLASH, TokenType.STAR):
            operator = self.previous()
            right = self.unary()
            expr = BinaryExpr(left=expr, operator=operator, right=right)

        return expr

    def unary(self) -> Expr:
        """解析一元表达式。

        包括 `!`、一元负号和 `await`。这些运算符会继续绑定右侧的一元表达式。
        """
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
        """解析调用和索引后缀。

        例如 `foo(1)[0]` 会从 `foo` 开始，不断追加调用或索引节点。
        """
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
        """解析函数调用参数列表。

        调用方已经消费了左括号，本函数读取参数直到右括号。
        """
        arguments: list[Expr] = []
        if not self.check(TokenType.RIGHT_PAREN):
            while True:
                arguments.append(self.expression())
                if not self.match(TokenType.COMMA):
                    break

        paren = self.consume(TokenType.RIGHT_PAREN, "函数调用参数后需要 ')'")
        return CallExpr(callee=callee, paren=paren, arguments=arguments)

    def finish_index(self, target: Expr) -> Expr:
        """解析索引读取表达式。

        调用方已经消费了左中括号，本函数读取索引表达式直到右中括号。
        """
        bracket = self.previous()
        index = self.expression()
        self.consume(TokenType.RIGHT_BRACKET, "索引表达式缺少 ']'")
        return IndexExpr(target=target, bracket=bracket, index=index)

    def primary(self) -> Expr:
        """解析最小表达式单元。

        字面量、变量、future 块、List/Map 字面量和括号表达式都在这一层处理。
        """
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
        if self.match(TokenType.LEFT_BRACE):
            return self.map_literal()
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
        """解析 List 字面量。"""
        elements: list[Expr] = []
        if not self.check(TokenType.RIGHT_BRACKET):
            while True:
                elements.append(self.expression())
                if not self.match(TokenType.COMMA):
                    break

        self.consume(TokenType.RIGHT_BRACKET, "列表字面量缺少 ']'")
        return ListExpr(elements)

    def map_literal(self) -> Expr:
        """解析 Map 字面量。

        每一项由 key 表达式、冒号和值表达式组成，例如 `{"name": "FR"}`。
        """
        entries: list[MapEntry] = []
        if not self.check(TokenType.RIGHT_BRACE):
            while True:
                key = self.expression()
                self.consume(TokenType.COLON, "Map key 后需要 ':'")
                value = self.expression()
                entries.append(MapEntry(key=key, value=value))
                if not self.match(TokenType.COMMA):
                    break

        self.consume(TokenType.RIGHT_BRACE, "Map 字面量缺少 '}'")
        return MapExpr(entries)

    def match(self, *types: TokenType) -> bool:
        """如果当前 Token 类型匹配任意给定类型，就消费并返回 True。"""
        for token_type in types:
            if self.check(token_type):
                self.advance()
                return True
        return False

    def consume(self, token_type: TokenType, message: str) -> Token:
        """消费指定类型的 Token，不匹配则抛出语法错误。"""
        if self.check(token_type):
            return self.advance()

        token = self.peek()
        raise ParserError(f"第 {token.line} 行，第 {token.column} 列：{message}")

    def check(self, token_type: TokenType) -> bool:
        """检查当前 Token 类型但不消费它。"""
        if self.is_at_end():
            return token_type is TokenType.EOF
        return self.peek().type is token_type

    def advance(self) -> Token:
        """消费当前 Token 并返回刚刚消费的 Token。"""
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def is_at_end(self) -> bool:
        """判断是否已经读到 EOF。"""
        return self.peek().type is TokenType.EOF

    def peek(self) -> Token:
        """返回当前 Token。"""
        return self.tokens[self.current]

    def previous(self) -> Token:
        """返回上一个已经消费的 Token。"""
        return self.tokens[self.current - 1]
