"""AST 节点定义。"""

from dataclasses import dataclass
from typing import Any

from .token import Token


class Expr:
    """表达式节点基类。"""


class Stmt:
    """语句节点基类。"""


@dataclass(frozen=True)
class LiteralExpr(Expr):
    """字面量表达式。"""

    value: Any


@dataclass(frozen=True)
class VariableExpr(Expr):
    """变量读取表达式。"""

    name: Token


@dataclass(frozen=True)
class ListExpr(Expr):
    """列表字面量表达式。"""

    elements: list[Expr]


@dataclass(frozen=True)
class MapEntry:
    """Map 字面量中的一组 key/value。"""

    key: Expr
    value: Expr


@dataclass(frozen=True)
class MapExpr(Expr):
    """Map 字面量表达式。"""

    entries: list[MapEntry]


@dataclass(frozen=True)
class IndexExpr(Expr):
    """索引读取表达式。"""

    target: Expr
    bracket: Token
    index: Expr


@dataclass(frozen=True)
class AssignExpr(Expr):
    """变量赋值表达式。"""

    name: Token
    value: Expr


@dataclass(frozen=True)
class IndexAssignExpr(Expr):
    """索引赋值表达式。"""

    target: Expr
    bracket: Token
    index: Expr
    value: Expr


@dataclass(frozen=True)
class GroupingExpr(Expr):
    """括号表达式。"""

    expression: Expr


@dataclass(frozen=True)
class UnaryExpr(Expr):
    """一元表达式。"""

    operator: Token
    right: Expr


@dataclass(frozen=True)
class AwaitExpr(Expr):
    """await 表达式。"""

    keyword: Token
    expression: Expr


@dataclass(frozen=True)
class FutureExpr(Expr):
    """future 块表达式。"""

    keyword: Token
    body: list[Stmt]


@dataclass(frozen=True)
class BinaryExpr(Expr):
    """二元表达式。"""

    left: Expr
    operator: Token
    right: Expr


@dataclass(frozen=True)
class CallExpr(Expr):
    """函数调用表达式。"""

    callee: Expr
    paren: Token
    arguments: list[Expr]


@dataclass(frozen=True)
class VarStmt(Stmt):
    """变量声明语句。"""

    name: Token
    initializer: Expr | None


@dataclass(frozen=True)
class PrintStmt(Stmt):
    """输出语句。"""

    expression: Expr


@dataclass(frozen=True)
class ExprStmt(Stmt):
    """表达式语句。"""

    expression: Expr


@dataclass(frozen=True)
class BlockStmt(Stmt):
    """代码块语句。"""

    statements: list[Stmt]


@dataclass(frozen=True)
class WhileStmt(Stmt):
    """while 循环语句。"""

    condition: Expr
    body: Stmt


@dataclass(frozen=True)
class IfStmt(Stmt):
    """if 条件分支语句。"""

    condition: Expr
    then_branch: Stmt
    else_branch: Stmt | None


@dataclass(frozen=True)
class FunctionStmt(Stmt):
    """函数声明语句。"""

    name: Token
    params: list[Token]
    body: list[Stmt]


@dataclass(frozen=True)
class ReturnStmt(Stmt):
    """return 返回语句。"""

    keyword: Token
    value: Expr | None


@dataclass(frozen=True)
class Program:
    """一个完整的 FRLanguage 程序。"""

    statements: list[Stmt]
