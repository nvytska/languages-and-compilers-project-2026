from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum, auto


def compilation_error(line, column, message):
    print(
        f"compilation error: line {line}:{column}: {message}",
        file=sys.stderr,
    )
    sys.exit(1)


I32_MIN = -(2 ** 31)
I32_MAX = 2 ** 31 - 1
I64_MIN = -(2 ** 63)
I64_MAX = 2 ** 63 - 1


class TokenKind(Enum):
    VAR = auto()
    LET = auto()
    IF = auto()
    ELSE = auto()
    TRUE = auto()
    FALSE = auto()
    MURR = auto()
    MEWI = auto()
    KSS = auto()
    MI = auto()
    READ = auto()
    PRINT = auto()
    TYPE_I32 = auto()
    TYPE_I64 = auto()
    TYPE_BOOL = auto()
    ASSIGN = auto()
    EQUAL = auto()
    NOT_EQUAL = auto()
    IDENTIFIER = auto()
    INTEGER = auto()
    LBRACE = auto()
    RBRACE = auto()
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    DOT = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    STRING = auto()
    EOF = auto()


@dataclass
class Token:
    kind: TokenKind
    text: str
    line: int
    column: int


CAT_I32 = "🐱".encode("utf-8")
CAT_I64 = "🐈".encode("utf-8")
CAT_BOOL = "😺".encode("utf-8")
CAT_READ = "📚".encode("utf-8")
CAT_PRINT = "🐾".encode("utf-8")


class Lexer:
    def __init__(self, source: bytes):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1

    def current_byte(self):
        if self.pos >= len(self.source):
            return None
        return self.source[self.pos]

    def advance(self):
        if self.pos >= len(self.source):
            return

        byte = self.source[self.pos]
        self.pos += 1

        if byte == ord("\n"):
            self.line += 1
            self.column = 1
        else:
            self.column += 1

    def skip_whitespace(self):
        while True:
            byte = self.current_byte()

            if byte is None:
                return

            if byte in (ord(" "), ord("\t"), ord("\r"), ord("\n")):
                self.advance()
                continue

            return

    def is_letter(self, byte):
        if byte is None:
            return False

        return (
            ord("a") <= byte <= ord("z")
            or ord("A") <= byte <= ord("Z")
            or byte == ord("_")
        )

    def is_digit(self, byte):
        if byte is None:
            return False

        return ord("0") <= byte <= ord("9")

    def is_identifier_part(self, byte):
        return self.is_letter(byte) or self.is_digit(byte)

    def lex_word(self):
        start = self.pos
        line = self.line
        column = self.column

        while self.is_identifier_part(self.current_byte()):
            self.advance()

        text_bytes = self.source[start:self.pos]
        text = text_bytes.decode("utf-8")

        keywords = {
            "var": TokenKind.VAR,
            "let": TokenKind.LET,
            "if": TokenKind.IF,
            "else": TokenKind.ELSE,
            "true": TokenKind.TRUE,
            "false": TokenKind.FALSE,
            "murr": TokenKind.MURR,
            "mewi": TokenKind.MEWI,
            "kss": TokenKind.KSS,
            "mi": TokenKind.MI,
            "meow": TokenKind.ASSIGN,
            "meowmeow": TokenKind.EQUAL,
            "woem": TokenKind.NOT_EQUAL,
        }

        kind = keywords.get(text, TokenKind.IDENTIFIER)

        return Token(kind, text, line, column)

    def lex_integer(self):
        start = self.pos
        line = self.line
        column = self.column

        while self.is_digit(self.current_byte()):
            self.advance()

        text = self.source[start:self.pos].decode("utf-8")

        return Token(TokenKind.INTEGER, text, line, column)

    def lex_string(self):
        line = self.line
        column = self.column
        self.advance()  # Opening quote.
        start = self.pos

        while True:
            byte = self.current_byte()
            if byte is None or byte in (ord("\n"), ord("\r")):
                compilation_error(line, column, "unterminated string literal")
            if byte == ord('"'):
                break
            # Count each UTF-8 character once, as lex_emoji does.
            if byte & 0xC0 == 0x80:
                self.pos += 1
            else:
                self.advance()

        try:
            text = self.source[start:self.pos].decode("utf-8")
        except UnicodeDecodeError:
            compilation_error(line, column, "invalid UTF-8 in string literal")
        self.advance()  # Closing quote.
        return Token(TokenKind.STRING, text, line, column)

    def match_bytes(self, value):
        end = self.pos + len(value)

        if self.source[self.pos:end] != value:
            return False

        self.pos = end
        self.column += 1

        return True

    def lex_emoji(self):
        line = self.line
        column = self.column

        if self.source.startswith(CAT_I32, self.pos):
            self.match_bytes(CAT_I32)
            return Token(TokenKind.TYPE_I32, "🐱", line, column)

        if self.source.startswith(CAT_I64, self.pos):
            self.match_bytes(CAT_I64)
            return Token(TokenKind.TYPE_I64, "🐈", line, column)

        if self.source.startswith(CAT_BOOL, self.pos):
            self.match_bytes(CAT_BOOL)
            return Token(TokenKind.TYPE_BOOL, "😺", line, column)

        if self.source.startswith(CAT_READ, self.pos):
            self.match_bytes(CAT_READ)
            return Token(TokenKind.READ, "📚", line, column)

        if self.source.startswith(CAT_PRINT, self.pos):
            self.match_bytes(CAT_PRINT)
            return Token(TokenKind.PRINT, "🐾", line, column)

        return None

    def next_token(self):
        self.skip_whitespace()

        if self.pos >= len(self.source):
            return Token(TokenKind.EOF, "", self.line, self.column)

        byte = self.current_byte()
        line = self.line
        column = self.column

        if self.is_letter(byte):
            return self.lex_word()

        if self.is_digit(byte):
            return self.lex_integer()

        if byte == ord('"'):
            return self.lex_string()

        punctuation = {
            ord("("): TokenKind.LPAREN,
            ord(")"): TokenKind.RPAREN,
            ord(","): TokenKind.COMMA,
            ord("."): TokenKind.DOT,
            ord("+"): TokenKind.PLUS,
            ord("-"): TokenKind.MINUS,
            ord("*"): TokenKind.STAR,
        }
        if byte in punctuation:
            self.advance()
            return Token(punctuation[byte], chr(byte), line, column)

        if byte == ord("{"):
            self.advance()
            return Token(TokenKind.LBRACE, "{", line, column)

        if byte == ord("}"):
            self.advance()
            return Token(TokenKind.RBRACE, "}", line, column)

        emoji_token = self.lex_emoji()

        if emoji_token is not None:
            return emoji_token

        bad_byte = self.current_byte()

        try:
            bad_text = bytes([bad_byte]).decode("utf-8")
        except UnicodeDecodeError:
            bad_text = f"byte {bad_byte}"

        compilation_error(
            line,
            column,
            f"unexpected character {bad_text}",
        )

    def tokenize(self):
        tokens = []

        while True:
            token = self.next_token()
            tokens.append(token)

            if token.kind == TokenKind.EOF:
                break

        return tokens


@dataclass
class ASTNode:
    line: int
    column: int

    def dump(self, indent=0):
        raise NotImplementedError


@dataclass
class ProgramNode(ASTNode):
    statements: list[StmtNode]

    def dump(self, indent=0):
        pad = "  " * indent
        lines = [f"{pad}Program"]

        for stmt in self.statements:
            lines.append(stmt.dump(indent + 1))

        return "\n".join(lines)


@dataclass
class StmtNode(ASTNode):
    pass


@dataclass
class ParameterNode(ASTNode):
    type_name: str
    name: str

    def dump(self, indent=0):
        pad = "  " * indent
        return "\n".join([
            f"{pad}Parameter",
            f"{pad}  type: {self.type_name}",
            f"{pad}  name: {self.name}",
        ])


@dataclass
class FunctionDeclNode(StmtNode):
    name: str
    parameters: list[ParameterNode]
    result_type: str
    body: list[StmtNode]

    def dump(self, indent=0):
        pad = "  " * indent

        lines = [
            f"{pad}FunctionDecl",
            f"{pad}  name: {self.name}",
            f"{pad}  parameters:",
        ]

        for parameter in self.parameters:
            lines.append(parameter.dump(indent + 2))

        lines.append(f"{pad}  result_type: {self.result_type}")
        lines.append(f"{pad}  body:")

        for stmt in self.body:
            lines.append(stmt.dump(indent + 2))

        return "\n".join(lines)


@dataclass
class ReturnNode(StmtNode):
    value: ExprNode

    def dump(self, indent=0):
        pad = "  " * indent
        return "\n".join([
            f"{pad}Return",
            f"{pad}  value:",
            self.value.dump(indent + 2),
        ])


@dataclass
class FieldDeclNode(ASTNode):
    mutable: bool
    type_name: str
    name: str

    def dump(self, indent=0):
        pad = "  " * indent
        return "\n".join([
            f"{pad}FieldDecl",
            f"{pad}  mutable: {str(self.mutable).lower()}",
            f"{pad}  type: {self.type_name}",
            f"{pad}  name: {self.name}",
        ])


@dataclass
class StructDeclNode(StmtNode):
    name: str
    fields: list[FieldDeclNode]
    methods: list[FunctionDeclNode]

    def dump(self, indent=0):
        pad = "  " * indent

        lines = [
            f"{pad}StructDecl",
            f"{pad}  name: {self.name}",
            f"{pad}  fields:",
        ]

        for field in self.fields:
            lines.append(field.dump(indent + 2))

        lines.append(f"{pad}  methods:")

        for method in self.methods:
            lines.append(method.dump(indent + 2))

        return "\n".join(lines)


@dataclass
class PrintNode(StmtNode):
    value: ExprNode

    def dump(self, indent=0):
        pad = "  " * indent
        return "\n".join([
            f"{pad}Print",
            f"{pad}  value:",
            self.value.dump(indent + 2),
        ])


@dataclass
class ExprStmtNode(StmtNode):
    expression: ExprNode

    def dump(self, indent=0):
        pad = "  " * indent
        return "\n".join([
            f"{pad}ExprStmt",
            self.expression.dump(indent + 1),
        ])


@dataclass
class VarDeclNode(StmtNode):
    mutable: bool
    type_name: str
    name: str
    value: ExprNode

    def dump(self, indent=0):
        pad = "  " * indent
        lines = [
            f"{pad}VarDecl",
            f"{pad}  mutable: {str(self.mutable).lower()}",
            f"{pad}  type: {self.type_name}",
            f"{pad}  name: {self.name}",
            f"{pad}  value:",
            self.value.dump(indent + 2),
        ]

        return "\n".join(lines)


@dataclass
class AssignmentNode(StmtNode):
    target: ExprNode
    value: ExprNode

    def dump(self, indent=0):
        pad = "  " * indent
        return "\n".join([
            f"{pad}Assignment",
            f"{pad}  target:",
            self.target.dump(indent + 2),
            f"{pad}  value:",
            self.value.dump(indent + 2),
        ])

@dataclass
class IfNode(StmtNode):
    condition: ExprNode
    then_body: list[StmtNode]
    else_body: list[StmtNode] | None

    def dump(self, indent=0):
        pad = "  " * indent
        lines = [
            f"{pad}If",
            f"{pad}  condition:",
            self.condition.dump(indent + 2),
            f"{pad}  then:",
        ]

        for stmt in self.then_body:
            lines.append(stmt.dump(indent + 2))

        if self.else_body is not None:
            lines.append(f"{pad}  else:")

            for stmt in self.else_body:
                lines.append(stmt.dump(indent + 2))

        return "\n".join(lines)


@dataclass
class ExprNode(ASTNode):
    pass


@dataclass
class IntegerLiteralNode(ExprNode):
    value: int

    def dump(self, indent=0):
        pad = "  " * indent
        return f"{pad}IntegerLiteral value: {self.value}"


@dataclass
class BooleanLiteralNode(ExprNode):
    value: bool

    def dump(self, indent=0):
        pad = "  " * indent
        return f"{pad}BooleanLiteral value: {str(self.value).lower()}"


@dataclass
class StringLiteralNode(ExprNode):
    value: str

    def dump(self, indent=0):
        pad = "  " * indent
        return f'{pad}StringLiteral value: "{self.value}"'


@dataclass
class IdentifierNode(ExprNode):
    name: str

    def dump(self, indent=0):
        pad = "  " * indent
        return f"{pad}Identifier name: {self.name}"


@dataclass
class ComparisonNode(ExprNode):
    operator: str
    left: ExprNode
    right: ExprNode

    def dump(self, indent=0):
        pad = "  " * indent
        return "\n".join([
            f"{pad}Comparison",
            f"{pad}  operator: {self.operator}",
            f"{pad}  left:",
            self.left.dump(indent + 2),
            f"{pad}  right:",
            self.right.dump(indent + 2),
        ])


@dataclass
class BinaryOpNode(ExprNode):
    operator: str
    left: ExprNode
    right: ExprNode

    def dump(self, indent=0):
        pad = "  " * indent
        return "\n".join([
            f"{pad}BinaryOp",
            f"{pad}  operator: {self.operator}",
            f"{pad}  left:",
            self.left.dump(indent + 2),
            f"{pad}  right:",
            self.right.dump(indent + 2),
        ])


@dataclass
class UnaryOpNode(ExprNode):
    operator: str
    operand: ExprNode

    def dump(self, indent=0):
        pad = "  " * indent
        return "\n".join([
            f"{pad}UnaryOp",
            f"{pad}  operator: {self.operator}",
            f"{pad}  operand:",
            self.operand.dump(indent + 2),
        ])


@dataclass
class CallNode(ExprNode):
    name: str
    arguments: list[ExprNode]

    def dump(self, indent=0):
        pad = "  " * indent

        lines = [
            f"{pad}Call",
            f"{pad}  name: {self.name}",
            f"{pad}  arguments:",
        ]

        for argument in self.arguments:
            lines.append(argument.dump(indent + 2))

        return "\n".join(lines)


@dataclass
class FieldAccessNode(ExprNode):
    object: ExprNode
    field_name: str

    def dump(self, indent=0):
        pad = "  " * indent

        return "\n".join([
            f"{pad}FieldAccess",
            f"{pad}  object:",
            self.object.dump(indent + 2),
            f"{pad}  field: {self.field_name}",
        ])


@dataclass
class MemberCallNode(ExprNode):
    object: ExprNode
    method_name: str
    arguments: list[ExprNode]

    def dump(self, indent=0):
        pad = "  " * indent

        lines = [
            f"{pad}MemberCall",
            f"{pad}  object:",
            self.object.dump(indent + 2),
            f"{pad}  method: {self.method_name}",
            f"{pad}  arguments:",
        ]

        for argument in self.arguments:
            lines.append(argument.dump(indent + 2))

        return "\n".join(lines)


@dataclass
class ObjectCreationNode(ExprNode):
    type_name: str
    arguments: list[ExprNode]

    def dump(self, indent=0):
        pad = "  " * indent

        lines = [
            f"{pad}ObjectCreation",
            f"{pad}  type: {self.type_name}",
            f"{pad}  values:",
        ]

        for argument in self.arguments:
            lines.append(argument.dump(indent + 2))

        return "\n".join(lines)


@dataclass
class ReadNode(ExprNode):

    def dump(self, indent=0):
        pad = "  " * indent
        return f"{pad}Read"


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.allow_object_creation = True

    def peek(self):
        return self.tokens[self.pos]

    def eat(self, expected_kind):
        token = self.peek()

        if token.kind != expected_kind:
            compilation_error(
                token.line,
                token.column,
                f"expected {expected_kind.name}, got {token.kind.name}",
            )

        self.pos += 1
        return token

    def check(self, kind):
        return self.peek().kind == kind

    def peek_next(self):
        if self.pos + 1 >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.pos + 1]

    def parse_type(self):
        token = self.peek()

        if token.kind == TokenKind.TYPE_I32:
            self.eat(TokenKind.TYPE_I32)
            return "i32"

        if token.kind == TokenKind.TYPE_I64:
            self.eat(TokenKind.TYPE_I64)
            return "i64"

        if token.kind == TokenKind.TYPE_BOOL:
            self.eat(TokenKind.TYPE_BOOL)
            return "bool"

        if token.kind == TokenKind.IDENTIFIER:
            token = self.eat(TokenKind.IDENTIFIER)
            return token.text

        compilation_error(
            token.line,
            token.column,
            "expected type",
        )

    def parse_program(self):
        items = []
        start = self.peek()

        while self.peek().kind != TokenKind.EOF:
            if self.peek().kind == TokenKind.MURR:
                items.append(self.parse_function_declaration())
            elif self.peek().kind == TokenKind.MEWI:
                items.append(self.parse_struct_declaration())
            else:
                items.append(self.parse_statement())

        self.eat(TokenKind.EOF)

        return ProgramNode(
            start.line,
            start.column,
            items,
        )

    def parse_parameter_list(self):
        parameters = []

        if self.check(TokenKind.RPAREN):
            return parameters

        while True:
            type_token = self.peek()
            type_name = self.parse_type()

            name_token = self.eat(TokenKind.IDENTIFIER)

            parameters.append(
                ParameterNode(
                    type_token.line,
                    type_token.column,
                    type_name,
                    name_token.text,
                )
            )

            if not self.check(TokenKind.COMMA):
                break

            self.eat(TokenKind.COMMA)

        return parameters

    def parse_function_declaration(self):
        start = self.eat(TokenKind.MURR)

        name_token = self.eat(TokenKind.IDENTIFIER)

        self.eat(TokenKind.LPAREN)
        parameters = self.parse_parameter_list()
        self.eat(TokenKind.RPAREN)

        self.eat(TokenKind.KSS)

        result_type = self.parse_type()

        body = self.parse_block()

        return FunctionDeclNode(
            start.line,
            start.column,
            name_token.text,
            parameters,
            result_type,
            body,
        )

    def parse_block(self, context="block"):
        self.eat(TokenKind.LBRACE)

        statements = []

        if self.check(TokenKind.RBRACE):
            token = self.peek()
            label = "block" if context == "block" else f"{context} block"
            compilation_error(
                token.line,
                token.column,
                f"{label} must contain at least one statement",
            )

        while not self.check(TokenKind.RBRACE):
            if self.check(TokenKind.EOF):
                token = self.peek()
                compilation_error(
                    token.line,
                    token.column,
                    "expected }",
                )

            statements.append(self.parse_statement())

        self.eat(TokenKind.RBRACE)

        return statements

    def parse_if_statement(self):
        if_token = self.eat(TokenKind.IF)

        condition = self.parse_expression(allow_object_creation=False)

        then_body = self.parse_block("if")

        else_body = None

        if self.check(TokenKind.ELSE):
            self.eat(TokenKind.ELSE)
            else_body = self.parse_block("else")

        return IfNode(
            if_token.line,
            if_token.column,
            condition,
            then_body,
            else_body,
        )

    def parse_field_declaration(self):
        start = self.peek()

        if self.check(TokenKind.VAR):
            self.eat(TokenKind.VAR)
            mutable = True
        else:
            self.eat(TokenKind.LET)
            mutable = False

        type_name = self.parse_type()

        name_token = self.eat(TokenKind.IDENTIFIER)

        return FieldDeclNode(
            start.line,
            start.column,
            mutable,
            type_name,
            name_token.text,
        )

    def parse_struct_declaration(self):
        start = self.eat(TokenKind.MEWI)

        name_token = self.eat(TokenKind.IDENTIFIER)

        self.eat(TokenKind.LBRACE)

        fields = []
        methods = []

        while not self.check(TokenKind.RBRACE):
            if self.check(TokenKind.EOF):
                token = self.peek()
                compilation_error(
                    token.line,
                    token.column,
                    "expected }",
                )

            if self.peek().kind in (TokenKind.VAR, TokenKind.LET):
                if methods:
                    token = self.peek()
                    compilation_error(token.line, token.column,
                                      "fields must be declared before member functions")
                fields.append(self.parse_field_declaration())
                continue

            if self.check(TokenKind.MURR):
                methods.append(self.parse_function_declaration())
                continue

            token = self.peek()

            compilation_error(
                token.line,
                token.column,
                f"unexpected token {token.text} in structure",
            )

        self.eat(TokenKind.RBRACE)

        if not fields:
            compilation_error(
                start.line,
                start.column,
                "structure must contain at least one field",
            )

        return StructDeclNode(
            start.line,
            start.column,
            name_token.text,
            fields,
            methods,
        )

    def parse_return_statement(self):
        token = self.eat(TokenKind.MI)

        value = self.parse_expression()

        return ReturnNode(
            token.line,
            token.column,
            value,
        )

    def parse_print_statement(self):
        token = self.eat(TokenKind.PRINT)

        self.eat(TokenKind.LPAREN)

        if self.check(TokenKind.STRING):
            string_token = self.eat(TokenKind.STRING)

            value = StringLiteralNode(
                string_token.line,
                string_token.column,
                string_token.text,
            )
        else:
            value = self.parse_expression()

        self.eat(TokenKind.RPAREN)

        return PrintNode(
            token.line,
            token.column,
            value,
        )

    def parse_variable_declaration(self):
        start = self.peek()

        if self.check(TokenKind.VAR):
            self.eat(TokenKind.VAR)
            mutable = True
        else:
            self.eat(TokenKind.LET)
            mutable = False

        type_name = self.parse_type()

        name_token = self.eat(TokenKind.IDENTIFIER)

        self.eat(TokenKind.ASSIGN)

        value = self.parse_expression()

        return VarDeclNode(
            start.line,
            start.column,
            mutable,
            type_name,
            name_token.text,
            value,
        )

    def parse_statement(self):
        token = self.peek()

        if token.kind in (TokenKind.VAR, TokenKind.LET):
            return self.parse_variable_declaration()

        if token.kind == TokenKind.IF:
            return self.parse_if_statement()

        if token.kind == TokenKind.MI:
            return self.parse_return_statement()

        if token.kind == TokenKind.PRINT:
            return self.parse_print_statement()

        if token.kind == TokenKind.IDENTIFIER:
            return self.parse_identifier_statement()

        compilation_error(
            token.line,
            token.column,
            f"unexpected token {token.text}",
        )

    def parse_identifier_statement(self):
        expression = self.parse_postfix_expression()

        if self.check(TokenKind.ASSIGN):
            assign_token = self.eat(TokenKind.ASSIGN)

            if not isinstance(
                expression,
                (IdentifierNode, FieldAccessNode),
            ):
                compilation_error(
                    assign_token.line,
                    assign_token.column,
                    "invalid assignment target",
                )

            value = self.parse_expression()

            return AssignmentNode(
                expression.line,
                expression.column,
                expression,
                value,
            )

        if isinstance(expression, (CallNode, MemberCallNode)):
            return ExprStmtNode(
                expression.line,
                expression.column,
                expression,
            )

        token = self.peek()

        compilation_error(
            token.line,
            token.column,
            "expected assignment or call",
        )

    def parse_expression(self, allow_object_creation=True):
        previous = self.allow_object_creation
        self.allow_object_creation = allow_object_creation
        try:
            return self.parse_comparison()
        finally:
            self.allow_object_creation = previous

    def parse_comparison(self):
        left = self.parse_additive()

        token = self.peek()

        if token.kind in (
            TokenKind.EQUAL,
            TokenKind.NOT_EQUAL,
        ):
            self.pos += 1

            right = self.parse_additive()

            operator = (
                "meowmeow"
                if token.kind == TokenKind.EQUAL
                else "woem"
            )

            return ComparisonNode(
                token.line,
                token.column,
                operator,
                left,
                right,
            )

        return left

    def parse_additive(self):
        expr = self.parse_multiplicative()

        while self.peek().kind in (
            TokenKind.PLUS,
            TokenKind.MINUS,
        ):
            token = self.peek()
            self.pos += 1

            right = self.parse_multiplicative()

            expr = BinaryOpNode(
                token.line,
                token.column,
                token.text,
                expr,
                right,
            )

        return expr

    def parse_multiplicative(self):
        expr = self.parse_unary()

        while self.peek().kind in (
            TokenKind.STAR,
        ):
            token = self.peek()
            self.pos += 1

            right = self.parse_unary()

            expr = BinaryOpNode(
                token.line,
                token.column,
                token.text,
                expr,
                right,
            )

        return expr

    def parse_unary(self):
        if self.check(TokenKind.MINUS):
            token = self.eat(TokenKind.MINUS)

            operand = self.parse_unary()

            return UnaryOpNode(
                token.line,
                token.column,
                "-",
                operand,
            )

        return self.parse_postfix_expression()

    def parse_argument_list(self):
        arguments = []

        if self.check(TokenKind.RPAREN):
            return arguments

        while True:
            arguments.append(
                self.parse_expression()
            )

            if not self.check(TokenKind.COMMA):
                break

            self.eat(TokenKind.COMMA)

        return arguments

    def parse_primary(self):
        token = self.peek()

        if token.kind == TokenKind.INTEGER:
            token = self.eat(TokenKind.INTEGER)

            try:
                value = int(token.text.lstrip("0") or "0")
            except ValueError:
                compilation_error(token.line, token.column,
                                  "integer constant does not fit in i64")
            return IntegerLiteralNode(token.line, token.column, value)

        if token.kind == TokenKind.TRUE:
            token = self.eat(TokenKind.TRUE)

            return BooleanLiteralNode(
                token.line,
                token.column,
                True,
            )

        if token.kind == TokenKind.FALSE:
            token = self.eat(TokenKind.FALSE)

            return BooleanLiteralNode(
                token.line,
                token.column,
                False,
            )

        if token.kind == TokenKind.READ:
            return self.parse_read_expression()

        if token.kind == TokenKind.IDENTIFIER:
            token = self.eat(TokenKind.IDENTIFIER)

            return IdentifierNode(
                token.line,
                token.column,
                token.text,
            )

        if token.kind == TokenKind.LPAREN:
            self.eat(TokenKind.LPAREN)

            expression = self.parse_expression()

            self.eat(TokenKind.RPAREN)

            return expression

        compilation_error(
            token.line,
            token.column,
            f"expected expression, got {token.kind.name}",
        )

    def parse_read_expression(self):
        token = self.eat(TokenKind.READ)

        self.eat(TokenKind.LPAREN)
        self.eat(TokenKind.RPAREN)

        return ReadNode(
            token.line,
            token.column,
        )

    def parse_postfix_expression(self):
        expr = self.parse_primary()

        while True:
            if (self.check(TokenKind.LBRACE)
                    and isinstance(expr, IdentifierNode)
                    and self.object_creation_allowed()):
                self.eat(TokenKind.LBRACE)

                arguments = []

                if not self.check(TokenKind.RBRACE):
                    while True:
                        arguments.append(
                            self.parse_expression()
                        )

                        if not self.check(TokenKind.COMMA):
                            break

                        self.eat(TokenKind.COMMA)

                self.eat(TokenKind.RBRACE)

                expr = ObjectCreationNode(
                    expr.line,
                    expr.column,
                    expr.name,
                    arguments,
                )

                continue

            # function call
            if self.check(TokenKind.LPAREN):
                if not isinstance(expr, IdentifierNode):
                    token = self.peek()

                    compilation_error(
                        token.line,
                        token.column,
                        "only a function name can be called directly",
                    )

                self.eat(TokenKind.LPAREN)

                arguments = self.parse_argument_list()

                self.eat(TokenKind.RPAREN)

                expr = CallNode(
                    expr.line,
                    expr.column,
                    expr.name,
                    arguments,
                )

                continue

            # field/member access
            if self.check(TokenKind.DOT):
                self.eat(TokenKind.DOT)

                name_token = self.eat(
                    TokenKind.IDENTIFIER
                )

                # member call
                if self.check(TokenKind.LPAREN):
                    self.eat(TokenKind.LPAREN)

                    arguments = self.parse_argument_list()

                    self.eat(TokenKind.RPAREN)

                    expr = MemberCallNode(
                        name_token.line,
                        name_token.column,
                        expr,
                        name_token.text,
                        arguments,
                    )

                # field access
                else:
                    expr = FieldAccessNode(
                        name_token.line,
                        name_token.column,
                        expr,
                        name_token.text,
                    )

                continue

            break

        return expr

    def object_creation_allowed(self):
        if self.allow_object_creation:
            return True
        # In an unparenthesized if condition, distinguish a constructor's braces
        # from the statement block using the token following the matching brace.
        depth = 0
        for index in range(self.pos, len(self.tokens)):
            kind = self.tokens[index].kind
            if kind == TokenKind.LBRACE:
                depth += 1
            elif kind == TokenKind.RBRACE:
                depth -= 1
                if depth == 0:
                    following = self.tokens[min(index + 1, len(self.tokens) - 1)].kind
                    return following in (
                        TokenKind.LBRACE, TokenKind.DOT, TokenKind.LPAREN,
                        TokenKind.PLUS, TokenKind.MINUS, TokenKind.STAR,
                        TokenKind.EQUAL, TokenKind.NOT_EQUAL,
                    )
            elif kind == TokenKind.EOF:
                break
        return False


@dataclass
class VariableSymbol:
    name: str
    type_name: str
    mutable: bool


@dataclass
class FunctionSymbol:
    name: str
    parameter_types: list[str]
    result_type: str


@dataclass
class FieldSymbol:
    name: str
    type_name: str
    mutable: bool
    index: int


@dataclass
class MemberFunctionSymbol:
    name: str
    parameter_types: list[str]
    result_type: str
    mutating: bool


@dataclass
class StructSymbol:
    name: str
    fields: dict[str, FieldSymbol]
    methods: dict[str, MemberFunctionSymbol]


class SemanticAnalyzer:
    def __init__(self):
        self.globals = {}
        self.functions = {}
        self.structs = {}

        self.scopes = []

        self.current_function = None
        self.current_struct = None
        # Code generation can use actual expression widths and required casts.
        self.expression_types = {}
        self.widenings = {}
        self.signed_literals = {}

    def analyze(self, program):
        self.collect_declarations(program)
        self.check_program(program)

    def collect_declarations(self, program):
        # Pass 1A: collect struct names first
        for item in program.statements:
            if isinstance(item, StructDeclNode):
                self.collect_struct_name(item)

        # Pass 1B: collect global function signatures
        for item in program.statements:
            if isinstance(item, FunctionDeclNode):
                self.collect_function_signature(item)

        # Pass 1C: collect struct fields and member function signatures
        for item in program.statements:
            if isinstance(item, StructDeclNode):
                self.collect_struct_members(item)
        self.check_struct_layouts(program)

    def check_struct_layouts(self, program):
        declarations = [node for node in program.statements if isinstance(node, StructDeclNode)]
        # Fields contain values, so recursive layouts have no finite size.
        visiting, complete = set(), set()

        def visit(node):
            visiting.add(node.name)
            for field in node.fields:
                if field.type_name in visiting:
                    compilation_error(field.line, field.column,
                                      "recursive structure fields have no finite size")
                if field.type_name in by_name and field.type_name not in complete:
                    visit(by_name[field.type_name])
            visiting.remove(node.name)
            complete.add(node.name)

        by_name = {node.name: node for node in declarations}
        for node in declarations:
            if node.name not in complete:
                visit(node)

    def collect_struct_name(self, node):
        if node.name in self.structs:
            compilation_error(
                node.line,
                node.column,
                f"structure '{node.name}' is already declared",
            )

        self.structs[node.name] = StructSymbol(
            name=node.name,
            fields={},
            methods={},
        )

    def collect_function_signature(self, node):
        if node.name in self.functions:
            compilation_error(
                node.line,
                node.column,
                f"function '{node.name}' is already declared",
            )

        self.check_duplicate_parameters(node.parameters)

        for parameter in node.parameters:
            self.require_valid_type(
                parameter.type_name,
                parameter.line,
                parameter.column,
            )

        self.require_valid_type(
            node.result_type,
            node.line,
            node.column,
        )

        parameter_types = [
            parameter.type_name
            for parameter in node.parameters
        ]

        self.functions[node.name] = FunctionSymbol(
            name=node.name,
            parameter_types=parameter_types,
            result_type=node.result_type,
        )

    def collect_struct_members(self, node):
        struct_symbol = self.structs[node.name]

        # fields
        for index, field in enumerate(node.fields):
            if field.name in struct_symbol.fields:
                compilation_error(
                    field.line,
                    field.column,
                    f"field '{field.name}' is already declared in structure '{node.name}'",
                )

            self.require_valid_type(field.type_name, field.line, field.column)

            struct_symbol.fields[field.name] = FieldSymbol(
                name=field.name,
                type_name=field.type_name,
                mutable=field.mutable,
                index=index,
            )

        # methods
        for method in node.methods:
            if method.name in struct_symbol.methods:
                compilation_error(
                    method.line,
                    method.column,
                    f"member function '{method.name}' is already declared in structure '{node.name}'",
                )

            self.check_duplicate_parameters(method.parameters)
            for parameter in method.parameters:
                self.require_valid_type(
                    parameter.type_name, parameter.line, parameter.column,
                )
            self.require_valid_type(method.result_type, method.line, method.column)

            parameter_types = [
                parameter.type_name
                for parameter in method.parameters
            ]

            struct_symbol.methods[method.name] = MemberFunctionSymbol(
                name=method.name,
                parameter_types=parameter_types,
                result_type=method.result_type,
                mutating=False,
            )

    def is_valid_type(self, type_name):
        if type_name in ("i32", "i64", "bool"):
            return True

        if type_name in self.structs:
            return True

        return False

    def require_valid_type(self, type_name, line, column):
        if not self.is_valid_type(type_name):
            compilation_error(
                line,
                column,
                f"unknown type '{type_name}'",
            )

    def check_duplicate_parameters(self, parameters):
        seen = set()

        for parameter in parameters:
            if parameter.name in seen:
                compilation_error(
                    parameter.line,
                    parameter.column,
                    f"parameter '{parameter.name}' is already declared",
                )

            seen.add(parameter.name)

    def check_program(self, program):
        initial_globals = dict(self.globals)
        while True:
            before = self.member_mutation_flags()
            self.globals.clear()
            self.globals.update(initial_globals)
            # Keep variables in declaration order, outside local scopes. Rechecking
            # propagates mutation through forward and recursive member calls.
            for item in program.statements:
                if isinstance(item, StructDeclNode):
                    self.check_struct_methods(item)
                elif isinstance(item, FunctionDeclNode):
                    self.check_function(item)
                else:
                    self.check_global_statement(item)
            if self.member_mutation_flags() == before:
                break

    def check_global_statement(self, node):
        if isinstance(node, VarDeclNode):
            self.check_global_variable_declaration(node)
            return

        self.check_statement(node)

    def check_global_variable_declaration(self, node):
        self.require_valid_type(
            node.type_name,
            node.line,
            node.column,
        )

        value_type = self.check_value(node.value, node.type_name)

        if not self.is_assignable(value_type, node.type_name):
            compilation_error(
                node.line,
                node.column,
                f"cannot initialize '{node.name}' of type "
                f"'{node.type_name}' with value of type '{value_type}'",
            )

        if node.name in self.globals:
            compilation_error(
                node.line,
                node.column,
                f"global variable '{node.name}' is already declared",
            )

        self.globals[node.name] = VariableSymbol(
            name=node.name,
            type_name=node.type_name,
            mutable=node.mutable,
        )

    def check_statement(self, node):
        if isinstance(node, VarDeclNode):
            self.check_variable_declaration(node)
            return

        if isinstance(node, AssignmentNode):
            self.check_assignment(node)
            return

        if isinstance(node, IfNode):
            self.check_if(node)
            return

        if isinstance(node, ReturnNode):
            self.check_return(node)
            return

        if isinstance(node, PrintNode):
            self.check_print(node)
            return

        if isinstance(node, ExprStmtNode):
            self.check_expression(node.expression)
            return

        compilation_error(
            node.line,
            node.column,
            "unsupported statement",
        )

    def check_variable_declaration(self, node):
        self.require_valid_type(
            node.type_name,
            node.line,
            node.column,
        )

        value_type = self.check_value(node.value, node.type_name)

        if not self.is_assignable(value_type, node.type_name):
            compilation_error(
                node.line,
                node.column,
                f"cannot initialize '{node.name}' of type "
                f"'{node.type_name}' with value of type '{value_type}'",
            )

        scope = self.scopes[-1]

        if node.name in scope:
            compilation_error(
                node.line,
                node.column,
                f"'{node.name}' is already declared in this scope",
            )

        scope[node.name] = VariableSymbol(
            name=node.name,
            type_name=node.type_name,
            mutable=node.mutable,
        )

    def is_integer_type(self, type_name):
        return type_name in ("i32", "i64")

    def integer_type_for_value(self, value, node):
        if I32_MIN <= value <= I32_MAX:
            return "i32"
        if I64_MIN <= value <= I64_MAX:
            return "i64"
        compilation_error(
            node.line, node.column,
            f"integer constant {value} does not fit in i64",
        )

    def is_assignable(self, source_type, target_type):
        return (source_type == target_type
                or (source_type == "i32" and target_type == "i64"))

    def check_value(self, node, expected_type):
        actual_type = self.check_expression(node)
        if actual_type == "i32" and expected_type == "i64":
            self.widenings[id(node)] = "i64"
        return actual_type

    def check_expression(self, node):
        return self.remember_type(node, self.expression_type(node))

    def remember_type(self, node, type_name):
        self.expression_types[id(node)] = type_name
        return type_name

    def type_of(self, node):
        return self.expression_types[id(node)]

    def expression_type(self, node):
        if isinstance(node, IntegerLiteralNode):
            return self.integer_type_for_value(node.value, node)

        if isinstance(node, BooleanLiteralNode):
            return "bool"

        if isinstance(node, StringLiteralNode):
            return "string"

        if isinstance(node, ReadNode):
            return "i32"

        if isinstance(node, IdentifierNode):
            return self.check_identifier(node)

        if isinstance(node, BinaryOpNode):
            return self.check_binary(node)

        if isinstance(node, ComparisonNode):
            return self.check_comparison(node)

        if isinstance(node, UnaryOpNode):
            return self.check_unary(node)

        if isinstance(node, CallNode):
            return self.check_call(node)

        if isinstance(node, ObjectCreationNode):
            return self.check_object_creation(node)

        if isinstance(node, FieldAccessNode):
            return self.check_field_access(node)

        if isinstance(node, MemberCallNode):
            return self.check_member_call(node)

        compilation_error(
            node.line,
            node.column,
            "unsupported expression",
        )

    def check_identifier(self, node):
        symbol = self.lookup_variable(node.name)

        if symbol is None:
            compilation_error(
                node.line,
                node.column,
                f"unknown name '{node.name}'",
            )

        return symbol.type_name

    def check_binary(self, node):
        left_type = self.check_expression(node.left)
        right_type = self.check_expression(node.right)
        if not self.is_integer_type(left_type) or not self.is_integer_type(right_type):
            compilation_error(
                node.line, node.column,
                f"operator '{node.operator}' requires integer operands",
            )
        result = "i64" if "i64" in (left_type, right_type) else "i32"
        if result == "i64":
            if left_type == "i32":
                self.widenings[id(node.left)] = "i64"
            if right_type == "i32":
                self.widenings[id(node.right)] = "i64"
        return result

    def check_comparison(self, node):
        left_type = self.check_expression(node.left)
        right_type = self.check_expression(node.right)
        if self.is_integer_type(left_type) and self.is_integer_type(right_type):
            if left_type != right_type:
                smaller = node.left if left_type == "i32" else node.right
                self.widenings[id(smaller)] = "i64"
        elif left_type != "bool" or right_type != "bool":
            compilation_error(
                node.line, node.column,
                f"cannot compare '{left_type}' with '{right_type}'",
            )
        return "bool"

    def check_unary(self, node):
        if node.operator != "-":
            compilation_error(
                node.line, node.column,
                f"unknown unary operator '{node.operator}'",
            )
        if isinstance(node.operand, IntegerLiteralNode):
            # Classify the signed literal as a whole, including -2**63, whose
            # positive magnitude is not itself a valid signed i64 literal.
            value = -node.operand.value
            result = self.integer_type_for_value(value, node)
            self.signed_literals[id(node)] = value
            self.remember_type(node.operand, result)
            return result
        operand_type = self.check_expression(node.operand)
        if not self.is_integer_type(operand_type):
            compilation_error(
                node.line, node.column,
                "unary '-' requires an integer operand",
            )
        return operand_type

    def push_scope(self):
        self.scopes.append({})

    def pop_scope(self):
        self.scopes.pop()

    def lookup_variable(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        if self.current_struct is not None:
            struct = self.structs[self.current_struct]
            if name in struct.fields:
                return struct.fields[name]
        return self.globals.get(name)

    def check_function(self, node):
        function_symbol = self.functions[node.name]

        previous_function = self.current_function
        previous_struct = self.current_struct

        self.current_function = function_symbol
        self.current_struct = None

        self.push_scope()

        try:
            # Parameters become local names
            for parameter in node.parameters:
                scope = self.scopes[-1]

                if parameter.name in scope:
                    compilation_error(
                        parameter.line,
                        parameter.column,
                        f"parameter '{parameter.name}' is already declared",
                    )

                scope[parameter.name] = VariableSymbol(
                    name=parameter.name,
                    type_name=parameter.type_name,
                    mutable=False,
                )

            for statement in node.body:
                self.check_statement(statement)

            if not self.block_guarantees_return(node.body):
                compilation_error(
                    node.line,
                    node.column,
                    f"function '{node.name}' may finish without mi",
                )
        finally:
            self.pop_scope()
            self.current_function = previous_function
            self.current_struct = previous_struct

    def block_guarantees_return(self, statements):
        for statement in statements:

            if isinstance(statement, ReturnNode):
                return True

            if isinstance(statement, IfNode):
                if (
                    statement.else_body is not None
                    and self.block_guarantees_return(statement.then_body)
                    and self.block_guarantees_return(statement.else_body)
                ):
                    return True

        return False

    def check_assignment(self, node):
        target_type = self.check_assignment_target(node.target)

        value_type = self.check_value(node.value, target_type)

        if not self.is_assignable(value_type, target_type):
            compilation_error(
                node.line,
                node.column,
                f"cannot assign value of type '{value_type}' "
                f"to target of type '{target_type}'",
            )

    def check_if(self, node):
        condition_type = self.check_expression(node.condition)
        if condition_type != "bool":
            compilation_error(
                node.condition.line, node.condition.column,
                f"if condition must be bool, got '{condition_type}'",
            )
        for body in (node.then_body, node.else_body):
            if body is None:
                continue
            self.push_scope()
            try:
                for statement in body:
                    self.check_statement(statement)
            finally:
                self.pop_scope()

    def check_return(self, node):
        if self.current_function is None:
            compilation_error(
                node.line,
                node.column,
                "mi may only be used inside a function",
            )

        expected_type = self.current_function.result_type
        value_type = self.check_value(node.value, expected_type)

        if not self.is_assignable(value_type, expected_type):
            compilation_error(
                node.line,
                node.column,
                f"function must return '{expected_type}', "
                f"got '{value_type}'",
            )

    def check_print(self, node):
        value_type = self.check_expression(node.value)

        if (
            value_type not in ("i32", "i64", "bool", "string")
            and value_type not in self.structs
        ):
            compilation_error(
                node.line,
                node.column,
                f"cannot print value of type '{value_type}'",
            )

    def check_call(self, node):
        if self.current_struct is not None:
            struct = self.structs[self.current_struct]
            if node.name in struct.methods:
                return self.check_implicit_member_call(node, struct.methods[node.name])

        if node.name not in self.functions:
            compilation_error(
                node.line,
                node.column,
                f"unknown function '{node.name}'",
            )

        function = self.functions[node.name]

        if len(node.arguments) != len(function.parameter_types):
            compilation_error(
                node.line,
                node.column,
                f"function '{node.name}' expects "
                f"{len(function.parameter_types)} arguments, "
                f"got {len(node.arguments)}",
            )

        for index, (argument, expected_type) in enumerate(
            zip(node.arguments, function.parameter_types),
            start=1,
        ):
            actual_type = self.check_value(argument, expected_type)

            if not self.is_assignable(actual_type, expected_type):
                compilation_error(
                    argument.line,
                    argument.column,
                    f"argument {index} of function '{node.name}' "
                    f"must have type '{expected_type}', "
                    f"got '{actual_type}'",
                )

        return function.result_type

    def check_object_creation(self, node):
        if node.type_name not in self.structs:
            compilation_error(
                node.line,
                node.column,
                f"unknown structure '{node.type_name}'",
            )

        struct = self.structs[node.type_name]

        fields = sorted(
            struct.fields.values(),
            key=lambda field: field.index,
        )

        if len(node.arguments) != len(fields):
            compilation_error(
                node.line,
                node.column,
                f"structure '{node.type_name}' expects "
                f"{len(fields)} values, got {len(node.arguments)}",
            )

        for argument, field in zip(node.arguments, fields):
            expected_type = field.type_name
            actual_type = self.check_value(argument, expected_type)

            if not self.is_assignable(actual_type, expected_type):
                compilation_error(
                    argument.line,
                    argument.column,
                    f"field '{field.name}' of structure "
                    f"'{node.type_name}' requires type "
                    f"'{expected_type}', got '{actual_type}'",
                )

        return node.type_name

    def check_field_access(self, node):
        object_type = self.check_expression(node.object)

        if object_type not in self.structs:
            compilation_error(
                node.line,
                node.column,
                f"type '{object_type}' has no fields",
            )

        struct = self.structs[object_type]

        if node.field_name not in struct.fields:
            compilation_error(
                node.line,
                node.column,
                f"structure '{object_type}' has no field "
                f"'{node.field_name}'",
            )

        field = struct.fields[node.field_name]

        return field.type_name

    def check_assignment_target(self, node):
        if isinstance(node, IdentifierNode):
            return self.check_mutable_identifier(node)

        if isinstance(node, FieldAccessNode):
            return self.check_mutable_field_access(node)

        compilation_error(
            node.line,
            node.column,
            "invalid assignment target",
        )

    def check_mutable_identifier(self, node):
        symbol = self.lookup_variable(node.name)

        if symbol is None:
            compilation_error(
                node.line,
                node.column,
                f"unknown name '{node.name}'",
            )

        if not symbol.mutable:
            compilation_error(
                node.line,
                node.column,
                f"cannot assign to constant '{node.name}'",
            )

        # If this is a field accessed directly inside a member function,
        # the member function mutates the current object.
        if isinstance(symbol, FieldSymbol):
            self.mark_current_member_mutating()

        return symbol.type_name

    def check_mutable_field_access(self, node):
        object_type = self.check_assignment_target(node.object)

        if object_type not in self.structs:
            compilation_error(
                node.line,
                node.column,
                f"type '{object_type}' has no fields",
            )

        struct = self.structs[object_type]

        if node.field_name not in struct.fields:
            compilation_error(
                node.line,
                node.column,
                f"structure '{object_type}' has no field "
                f"'{node.field_name}'",
            )

        field = struct.fields[node.field_name]

        if not field.mutable:
            compilation_error(
                node.line,
                node.column,
                f"cannot assign through constant field "
                f"'{node.field_name}'",
            )

        return field.type_name

    def mark_current_member_mutating(self):
        if (
            self.current_struct is not None
            and isinstance(
                self.current_function,
                MemberFunctionSymbol,
            )
        ):
            self.current_function.mutating = True

    def check_struct_methods(self, struct_node):
        for method in struct_node.methods:
            self.check_member_function(
                struct_node.name,
                method,
            )

    def check_member_function(self, struct_name, node):
        struct_symbol = self.structs[struct_name]
        method_symbol = struct_symbol.methods[node.name]

        previous_function = self.current_function
        previous_struct = self.current_struct

        self.current_function = method_symbol
        self.current_struct = struct_name

        self.push_scope()

        try:
            # Parameters are local names
            for parameter in node.parameters:
                scope = self.scopes[-1]

                if parameter.name in scope:
                    compilation_error(
                        parameter.line,
                        parameter.column,
                        f"parameter '{parameter.name}' is already declared",
                    )

                scope[parameter.name] = VariableSymbol(
                    name=parameter.name,
                    type_name=parameter.type_name,
                    mutable=False,
                )

            for statement in node.body:
                self.check_statement(statement)

            if not self.block_guarantees_return(node.body):
                compilation_error(
                    node.line,
                    node.column,
                    f"member function '{node.name}' may finish without mi",
                )
        finally:
            self.pop_scope()
            self.current_function = previous_function
            self.current_struct = previous_struct

    def check_mutable_receiver(self, node):
        if isinstance(node, IdentifierNode):
            symbol = self.lookup_variable(node.name)

            if symbol is None:
                compilation_error(
                    node.line,
                    node.column,
                    f"unknown name '{node.name}'",
                )

            if not symbol.mutable:
                compilation_error(
                    node.line,
                    node.column,
                    f"cannot call mutating member function "
                    f"on constant '{node.name}'",
                )

            if isinstance(symbol, FieldSymbol):
                self.mark_current_member_mutating()

            return symbol.type_name

        if isinstance(node, FieldAccessNode):
            return self.check_mutable_field_access(node)

        compilation_error(
            node.line,
            node.column,
            "mutating member function requires a mutable object",
        )

    def check_implicit_member_call(self, node, method):
        if len(node.arguments) != len(method.parameter_types):
            compilation_error(
                node.line,
                node.column,
                f"member function '{node.name}' expects "
                f"{len(method.parameter_types)} arguments, "
                f"got {len(node.arguments)}",
            )

        for index, (argument, expected_type) in enumerate(
            zip(node.arguments, method.parameter_types),
            start=1,
        ):
            actual_type = self.check_value(argument, expected_type)

            if not self.is_assignable(actual_type, expected_type):
                compilation_error(
                    argument.line,
                    argument.column,
                    f"argument {index} of member function "
                    f"'{node.name}' must have type "
                    f"'{expected_type}', got '{actual_type}'",
                )

        if method.mutating:
            self.mark_current_member_mutating()

        return method.result_type

    def member_mutation_flags(self):
        return tuple(
            method.mutating
            for struct in self.structs.values()
            for method in struct.methods.values()
        )

    def check_member_call(self, node):
        object_type = self.check_expression(node.object)

        if object_type not in self.structs:
            compilation_error(
                node.line,
                node.column,
                f"type '{object_type}' has no member functions",
            )

        struct = self.structs[object_type]

        if node.method_name not in struct.methods:
            compilation_error(
                node.line,
                node.column,
                f"structure '{object_type}' has no member function "
                f"'{node.method_name}'",
            )

        method = struct.methods[node.method_name]

        if len(node.arguments) != len(method.parameter_types):
            compilation_error(
                node.line,
                node.column,
                f"member function '{node.method_name}' expects "
                f"{len(method.parameter_types)} arguments, "
                f"got {len(node.arguments)}",
            )

        for index, (argument, expected_type) in enumerate(
            zip(node.arguments, method.parameter_types),
            start=1,
        ):
            actual_type = self.check_value(argument, expected_type)

            if not self.is_assignable(actual_type, expected_type):
                compilation_error(
                    argument.line,
                    argument.column,
                    f"argument {index} of member function "
                    f"'{node.method_name}' must have type "
                    f"'{expected_type}', got '{actual_type}'",
                )

        if method.mutating:
            self.check_mutable_receiver(node.object)

        return method.result_type


@dataclass
class LLVMVariable:
    pointer: object
    type_name: str


class CodeGenerator:
    def __init__(self, semantic):
        # AST inspection and semantic checks do not require llvmlite.
        global ir, llvm
        from llvmlite import ir
        import llvmlite.binding as llvm

        self.semantic = semantic

        self.module = ir.Module(name="mew_module", context=ir.Context())
        self.module.triple = llvm.get_default_triple()

        self.i1 = ir.IntType(1)
        self.i8 = ir.IntType(8)
        self.i32 = ir.IntType(32)
        self.i64 = ir.IntType(64)

        self.builder = None
        self.current_function = None
        self.current_result_type = None

        self.scopes = []
        self.global_variables = {}

        self.generating_global = False

        self.functions = {}
        self.struct_types = {}
        self.member_functions = {}
        self.current_struct_name = None
        self.current_self_pointer = None

        self.setup_runtime()

    def llvm_type(self, type_name):
        if type_name == "i32":
            return self.i32

        if type_name == "i64":
            return self.i64

        if type_name == "bool":
            return self.i1

        if type_name in self.struct_types:
            return self.struct_types[type_name]

        raise RuntimeError(
            f"internal compiler error: unknown type '{type_name}'"
        )

    def setup_runtime(self):
        i8_pointer = self.i8.as_pointer()

        # printf(const char *fmt, ...)
        # scanf(const char *fmt, ...)
        c_vararg_type = ir.FunctionType(
            self.i32,
            [i8_pointer],
            var_arg=True,
        )

        self.printf = ir.Function(
            self.module,
            c_vararg_type,
            name="printf",
        )

        self.scanf = ir.Function(
            self.module,
            c_vararg_type,
            name="scanf",
        )

        # Already used for overflow handling
        puts_type = ir.FunctionType(
            self.i32,
            [i8_pointer],
        )

        self.puts = ir.Function(
            self.module,
            puts_type,
            name="puts",
        )

        exit_type = ir.FunctionType(
            ir.VoidType(),
            [self.i32],
        )

        self.exit_function = ir.Function(
            self.module,
            exit_type,
            name="exit",
        )

        self.global_string_counter = 0
        self.global_string_cache = {}

        # scanf
        self.fmt_read_i32 = self.create_global_string("%d")

        # normal print
        self.fmt_i32 = self.create_global_string("%d")
        self.fmt_i32_line = self.create_global_string("%d\n")

        self.fmt_i64 = self.create_global_string("%lld")
        self.fmt_i64_line = self.create_global_string("%lld\n")

        self.fmt_string = self.create_global_string("%s")
        self.fmt_string_line = self.create_global_string("%s\n")

        self.true_string = self.create_global_string("true")
        self.false_string = self.create_global_string("false")

        self.overflow_message = self.create_global_string(
            "runtime error: integer overflow"
        )

    def create_global_string(self, text):
        if text in self.global_string_cache:
            return self.global_string_cache[text]

        data = text.encode("utf-8") + b"\0"

        array_type = ir.ArrayType(
            self.i8,
            len(data),
        )

        name = f"mew_string_{self.global_string_counter}"
        self.global_string_counter += 1

        global_string = ir.GlobalVariable(
            self.module,
            array_type,
            name=name,
        )

        global_string.linkage = "private"
        global_string.global_constant = True

        global_string.initializer = ir.Constant(
            array_type,
            bytearray(data),
        )

        self.global_string_cache[text] = global_string

        return global_string

    def widen_value(
        self,
        value,
        source_type,
        target_type,
    ):
        if source_type == target_type:
            return value

        if source_type == "i32" and target_type == "i64":
            return self.builder.sext(
                value,
                self.i64,
                name="widen_i32_to_i64",
            )

        raise RuntimeError(
            f"internal compiler error: "
            f"cannot widen {source_type} to {target_type}"
        )

    def generate_expression(self, node):
        if isinstance(node, IntegerLiteralNode):
            type_name = self.semantic.type_of(node)

            return ir.Constant(
                self.llvm_type(type_name),
                node.value,
            )

        if isinstance(node, BooleanLiteralNode):
            return ir.Constant(
                self.i1,
                1 if node.value else 0,
            )

        if isinstance(node, (IdentifierNode, FieldAccessNode)):
            return self.builder.load(self.generate_address(node), name="load_value")

        if isinstance(node, ObjectCreationNode):
            return self.generate_object_creation(node)

        if isinstance(node, MemberCallNode):
            return self.generate_member_call(node)

        if isinstance(node, ReadNode):
            return self.generate_read(node)

        if isinstance(node, CallNode):
            return self.generate_call(node)

        if isinstance(node, BinaryOpNode):
            return self.generate_binary(node)

        if isinstance(node, ComparisonNode):
            return self.generate_comparison(node)

        if isinstance(node, UnaryOpNode):
            return self.generate_unary(node)

        compilation_error(node.line, node.column,
                          f"LLVM generation for {type(node).__name__} is not implemented yet")

    def get_overflow_intrinsic(
        self,
        operator,
        llvm_type,
    ):
        names = {
            "+": "sadd",
            "-": "ssub",
            "*": "smul",
        }

        if operator not in names:
            raise RuntimeError(
                f"unknown checked operator '{operator}'"
            )

        operation = names[operator]

        name = (
            f"llvm.{operation}.with.overflow."
            f"i{llvm_type.width}"
        )

        if name in self.module.globals:
            return self.module.globals[name]

        result_type = ir.LiteralStructType([
            llvm_type,
            self.i1,
        ])

        function_type = ir.FunctionType(
            result_type,
            [llvm_type, llvm_type],
        )

        return ir.Function(
            self.module,
            function_type,
            name=name,
        )

    def emit_checked_binary(
        self,
        operator,
        left,
        right,
        type_name,
    ):
        llvm_type = self.llvm_type(type_name)

        intrinsic = self.get_overflow_intrinsic(
            operator,
            llvm_type,
        )

        pair = self.builder.call(
            intrinsic,
            [left, right],
            name="checked_arithmetic",
        )

        result = self.builder.extract_value(
            pair,
            0,
            name="arithmetic_result",
        )

        overflow = self.builder.extract_value(
            pair,
            1,
            name="overflow",
        )

        function = self.builder.function

        overflow_block = function.append_basic_block(
            "overflow"
        )

        continue_block = function.append_basic_block(
            "overflow_continue"
        )

        self.builder.cbranch(
            overflow,
            overflow_block,
            continue_block,
        )

        # overflow
        self.builder.position_at_end(
            overflow_block
        )

        message_pointer = self.builder.bitcast(
            self.overflow_message,
            self.i8.as_pointer(),
        )

        self.builder.call(
            self.puts,
            [message_pointer],
        )

        self.builder.call(
            self.exit_function,
            [ir.Constant(self.i32, 1)],
        )

        self.builder.unreachable()

        # normal execution
        self.builder.position_at_end(
            continue_block
        )

        return result

    def generate_binary(self, node):
        left = self.generate_expression(
            node.left
        )

        right = self.generate_expression(
            node.right
        )

        left_type = self.semantic.type_of(
            node.left
        )

        right_type = self.semantic.type_of(
            node.right
        )

        result_type = self.semantic.type_of(
            node
        )

        left = self.widen_value(
            left,
            left_type,
            result_type,
        )

        right = self.widen_value(
            right,
            right_type,
            result_type,
        )

        return self.emit_checked_binary(
            node.operator,
            left,
            right,
            result_type,
        )

    def generate_comparison(self, node):
        left = self.generate_expression(
            node.left
        )

        right = self.generate_expression(
            node.right
        )

        left_type = self.semantic.type_of(
            node.left
        )

        right_type = self.semantic.type_of(
            node.right
        )

        if (
            left_type in ("i32", "i64")
            and right_type in ("i32", "i64")
        ):
            compare_type = (
                "i64"
                if "i64" in (left_type, right_type)
                else "i32"
            )

            left = self.widen_value(
                left,
                left_type,
                compare_type,
            )

            right = self.widen_value(
                right,
                right_type,
                compare_type,
            )

        if node.operator == "meowmeow":
            return self.builder.icmp_signed(
                "==",
                left,
                right,
                name="compare_equal",
            )

        if node.operator == "woem":
            return self.builder.icmp_signed(
                "!=",
                left,
                right,
                name="compare_not_equal",
            )

        raise RuntimeError(
            f"unknown comparison '{node.operator}'"
        )

    def generate_variable_declaration(self, node):
        value = self.generate_expression(
            node.value
        )

        value_type = self.semantic.type_of(
            node.value
        )

        value = self.widen_value(
            value,
            value_type,
            node.type_name,
        )

        # Global
        if self.generating_global:
            variable = self.global_variables[
                node.name
            ]

            self.builder.store(
                value,
                variable.pointer,
            )

            return

        # Local
        llvm_type = self.llvm_type(
            node.type_name
        )

        pointer = self.create_entry_alloca(
            llvm_type,
            name=node.name,
        )

        self.builder.store(
            value,
            pointer,
        )

        self.scopes[-1][node.name] = LLVMVariable(
            pointer=pointer,
            type_name=node.type_name,
        )

    def generate_assignment(self, node):
        pointer = self.generate_address(node.target)
        value = self.generate_expression(node.value)
        value = self.widen_value(value, self.semantic.type_of(node.value),
                                 self.address_type(node.target))
        self.builder.store(value, pointer)

    def generate_unary(self, node):
        if node.operator != "-":
            raise RuntimeError(
                f"unknown unary operator '{node.operator}'"
            )

        result_type = self.semantic.type_of(node)

        # -2147483648 should become an i32 constant directly.
        if isinstance(
            node.operand,
            IntegerLiteralNode,
        ):
            return ir.Constant(
                self.llvm_type(result_type),
                -node.operand.value,
            )

        value = self.generate_expression(
            node.operand
        )

        source_type = self.semantic.type_of(
            node.operand
        )

        value = self.widen_value(
            value,
            source_type,
            result_type,
        )

        zero = ir.Constant(
            self.llvm_type(result_type),
            0,
        )

        return self.emit_checked_binary(
            "-",
            zero,
            value,
            result_type,
        )

    def generate(self, program):
        self.declare_struct_types(program)
        self.declare_globals(program)
        self.declare_functions(program)
        self.declare_member_functions(program)
        self.generate_function_bodies(program)
        self.generate_member_function_bodies(program)
        self.generate_main(program)
        module_text = str(self.module)
        llvm.parse_assembly(module_text).verify()
        return module_text

    def declare_globals(self, program):
        for node in program.statements:
            if isinstance(node, VarDeclNode):
                global_value = ir.GlobalVariable(
                    self.module, self.llvm_type(node.type_name), name=f"mew_global_{node.name}",
                )
                global_value.linkage = "internal"
                global_value.initializer = ir.Constant(self.llvm_type(node.type_name), None)
                self.global_variables[node.name] = LLVMVariable(global_value, node.type_name)

    def generate_main(self, program):
        main_type = ir.FunctionType(self.i32, [])
        self.current_function = ir.Function(self.module, main_type, name="main")
        self.builder = ir.IRBuilder(self.current_function.append_basic_block("entry"))
        self.push_scope()
        try:
            for node in program.statements:
                if isinstance(node, (FunctionDeclNode, StructDeclNode)):
                    continue
                self.generating_global = True
                self.generate_statement(node)
            self.builder.ret(ir.Constant(self.i32, 0))
        finally:
            self.pop_scope()
            self.generating_global = False

    def push_scope(self):
        self.scopes.append({})

    def pop_scope(self):
        self.scopes.pop()

    def lookup_variable(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return self.global_variables[name]

    def generate_statement(self, node):
        if isinstance(node, VarDeclNode):
            self.generate_variable_declaration(node)
        elif isinstance(node, AssignmentNode):
            self.generate_assignment(node)
        elif isinstance(node, IfNode):
            self.generate_if(node)
        elif isinstance(node, PrintNode):
            self.generate_print(node)
        elif isinstance(node, ReturnNode):
            self.generate_return(node)
        elif isinstance(node, ExprStmtNode):
            self.generate_expression(node.expression)
        else:
            compilation_error(node.line, node.column,
                              f"LLVM generation for {type(node).__name__} is not implemented yet")

    def generate_block(self, statements):
        previous = self.generating_global
        self.generating_global = False
        self.push_scope()
        try:
            for node in statements:
                if self.builder.block.is_terminated:
                    break
                self.generate_statement(node)
        finally:
            self.pop_scope()
            self.generating_global = previous

    def generate_if(self, node):
        condition = self.generate_expression(node.condition)
        function = self.current_function
        then_block = function.append_basic_block("if_then")
        else_block = function.append_basic_block("if_else") if node.else_body is not None else None
        end_block = function.append_basic_block("if_end")
        self.builder.cbranch(condition, then_block, else_block or end_block)
        self.builder.position_at_end(then_block)
        self.generate_block(node.then_body)
        then_terminated = self.builder.block.is_terminated
        if not then_terminated:
            self.builder.branch(end_block)
        if else_block is not None:
            self.builder.position_at_end(else_block)
            self.generate_block(node.else_body)
            else_terminated = self.builder.block.is_terminated
            if not else_terminated:
                self.builder.branch(end_block)
        self.builder.position_at_end(end_block)
        if else_block is not None and then_terminated and else_terminated:
            self.builder.unreachable()

    def declare_functions(self, program):
        for item in program.statements:
            if not isinstance(item, FunctionDeclNode):
                continue

            parameter_types = [
                self.llvm_type(parameter.type_name)
                for parameter in item.parameters
            ]

            result_type = self.llvm_type(
                item.result_type
            )

            function_type = ir.FunctionType(
                result_type,
                parameter_types,
            )

            llvm_function = ir.Function(
                self.module,
                function_type,
                name=f"mew_fn_{item.name}",
            )

            self.functions[item.name] = llvm_function

    def generate_function_bodies(self, program):
        for item in program.statements:
            if isinstance(item, FunctionDeclNode):
                self.generate_function_body(item)

    def generate_function_body(self, node):
        llvm_function = self.functions[node.name]

        entry = llvm_function.append_basic_block("entry")

        previous_builder = self.builder
        previous_function = self.current_function
        previous_scopes = self.scopes
        previous_result_type = self.current_result_type
        previous_generating_global = self.generating_global
        self.generating_global = False

        self.builder = ir.IRBuilder(entry)
        self.current_function = llvm_function
        self.current_result_type = node.result_type
        self.scopes = []

        self.push_scope()

        try:
            for parameter_node, llvm_argument in zip(
                node.parameters,
                llvm_function.args,
            ):
                llvm_argument.name = parameter_node.name

                pointer = self.create_entry_alloca(
                    self.llvm_type(parameter_node.type_name),
                    name=f"{parameter_node.name}_slot",
                )

                self.builder.store(
                    llvm_argument,
                    pointer,
                )

                self.scopes[-1][parameter_node.name] = LLVMVariable(
                    pointer=pointer,
                    type_name=parameter_node.type_name,
                )

            for statement in node.body:
                if self.builder.block.is_terminated:
                    break

                self.generate_statement(statement)

            if not self.builder.block.is_terminated:
                self.builder.unreachable()
        finally:
            self.pop_scope()
            self.builder = previous_builder
            self.current_function = previous_function
            self.current_result_type = previous_result_type
            self.scopes = previous_scopes
            self.generating_global = previous_generating_global

    def generate_return(self, node):
        value = self.generate_expression(
            node.value
        )

        source_type = self.semantic.type_of(
            node.value
        )

        value = self.widen_value(
            value,
            source_type,
            self.current_result_type,
        )

        self.builder.ret(value)

    def generate_call(self, node):
        if self.current_struct_name is not None:
            struct = self.semantic.structs[self.current_struct_name]
            if node.name in struct.methods:
                return self.generate_implicit_member_call(node)
        llvm_function = self.functions[node.name]
        function_symbol = self.semantic.functions[node.name]

        arguments = []

        for argument_node, expected_type in zip(
            node.arguments,
            function_symbol.parameter_types,
        ):
            value = self.generate_expression(
                argument_node
            )

            actual_type = self.semantic.type_of(
                argument_node
            )

            value = self.widen_value(
                value,
                actual_type,
                expected_type,
            )

            arguments.append(value)

        return self.builder.call(
            llvm_function,
            arguments,
            name=f"call_{node.name}",
        )

    def declare_struct_types(self, program):
        declarations = [node for node in program.statements if isinstance(node, StructDeclNode)]
        for node in declarations:
            self.struct_types[node.name] = self.module.context.get_identified_type(
                f"mew_struct_{node.name}",
            )
        for node in declarations:
            fields = sorted(self.semantic.structs[node.name].fields.values(),
                            key=lambda field: field.index)
            self.struct_types[node.name].set_body(*(self.llvm_type(field.type_name) for field in fields))

    def create_entry_alloca(self, llvm_type, name):
        entry = self.current_function.entry_basic_block
        allocator = ir.IRBuilder(entry)
        allocator.position_at_start(entry)
        pointer = allocator.alloca(llvm_type, name=name)
        if self.builder.block is entry:
            self.builder.position_at_end(entry)
        return pointer

    def address_type(self, node):
        if isinstance(node, IdentifierNode):
            local = self.lookup_local_variable(node.name)
            if local is not None:
                return local.type_name
            if self.current_struct_name is not None:
                fields = self.semantic.structs[self.current_struct_name].fields
                if node.name in fields:
                    return fields[node.name].type_name
            return self.global_variables[node.name].type_name
        if isinstance(node, FieldAccessNode):
            object_type = self.address_type(node.object)
            return self.semantic.structs[object_type].fields[node.field_name].type_name
        return self.semantic.type_of(node)

    def generate_field_address(self, node):
        object_type = self.address_type(node.object)
        pointer = self.generate_receiver_pointer(node.object)
        field = self.semantic.structs[object_type].fields[node.field_name]
        return self.builder.gep(
            pointer, [ir.Constant(self.i32, 0), ir.Constant(self.i32, field.index)],
            inbounds=True,
            name=f"field_{node.field_name}_ptr",
        )

    def generate_object_creation(self, node):
        struct_type = self.struct_types[node.type_name]
        pointer = self.create_entry_alloca(struct_type, "object_temp")
        fields = sorted(self.semantic.structs[node.type_name].fields.values(),
                        key=lambda field: field.index)
        for argument, field in zip(node.arguments, fields):
            value = self.generate_expression(argument)
            value = self.widen_value(value, self.semantic.type_of(argument), field.type_name)
            field_pointer = self.builder.gep(
                pointer, [ir.Constant(self.i32, 0), ir.Constant(self.i32, field.index)],
                inbounds=True,
            )
            self.builder.store(value, field_pointer)
        return self.builder.load(pointer, name="object_value")

    def declare_member_functions(self, program):
        for struct_node in program.statements:
            if not isinstance(struct_node, StructDeclNode):
                continue

            struct_type = self.struct_types[
                struct_node.name
            ]

            self_pointer_type = struct_type.as_pointer()

            for method in struct_node.methods:
                parameter_types = [
                    self_pointer_type
                ]

                parameter_types.extend(
                    self.llvm_type(parameter.type_name)
                    for parameter in method.parameters
                )

                result_type = self.llvm_type(
                    method.result_type
                )

                function_type = ir.FunctionType(
                    result_type,
                    parameter_types,
                )

                llvm_function = ir.Function(
                    self.module,
                    function_type,
                    name=self.module.get_unique_name(
                        f"mew_method_"
                        f"{struct_node.name}_"
                        f"{method.name}"
                    ),
                )

                self.member_functions[
                    (struct_node.name, method.name)
                ] = llvm_function

    def generate_member_function_bodies(self, program):
        for struct_node in program.statements:
            if not isinstance(struct_node, StructDeclNode):
                continue

            for method in struct_node.methods:
                self.generate_member_function_body(
                    struct_node,
                    method,
                )

    def generate_member_function_body(
        self,
        struct_node,
        method_node,
    ):
        llvm_function = self.member_functions[
            (struct_node.name, method_node.name)
        ]

        entry = llvm_function.append_basic_block(
            "entry"
        )

        previous_generating_global = self.generating_global
        self.generating_global = False
        previous_builder = self.builder
        previous_function = self.current_function
        previous_result_type = self.current_result_type
        previous_scopes = self.scopes

        previous_struct = self.current_struct_name
        previous_self = self.current_self_pointer

        self.builder = ir.IRBuilder(entry)
        self.current_function = llvm_function
        self.current_result_type = method_node.result_type

        self.current_struct_name = struct_node.name
        self.current_self_pointer = llvm_function.args[0]

        self.current_self_pointer.name = "self"

        self.scopes = []
        self.push_scope()

        try:
            # args[0] = self
            # args[1:] = explicit parameters
            for parameter_node, llvm_argument in zip(
                method_node.parameters,
                llvm_function.args[1:],
            ):
                llvm_argument.name = parameter_node.name

                pointer = self.create_entry_alloca(
                    self.llvm_type(parameter_node.type_name),
                    f"{parameter_node.name}_slot",
                )

                self.builder.store(
                    llvm_argument,
                    pointer,
                )

                self.scopes[-1][parameter_node.name] = LLVMVariable(
                    pointer=pointer,
                    type_name=parameter_node.type_name,
                )

            for statement in method_node.body:
                if self.builder.block.is_terminated:
                    break

                self.generate_statement(statement)

            if not self.builder.block.is_terminated:
                self.builder.unreachable()
        finally:
            self.pop_scope()
            self.builder = previous_builder
            self.current_function = previous_function
            self.current_result_type = previous_result_type
            self.scopes = previous_scopes
            self.current_struct_name = previous_struct
            self.current_self_pointer = previous_self
            self.generating_global = previous_generating_global

    def lookup_local_variable(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]

        return None

    def generate_implicit_field_address(
        self,
        field_name,
    ):
        struct_symbol = self.semantic.structs[
            self.current_struct_name
        ]

        field = struct_symbol.fields[
            field_name
        ]

        struct_type = self.struct_types[
            self.current_struct_name
        ]

        zero = ir.Constant(self.i32, 0)

        index = ir.Constant(
            self.i32,
            field.index,
        )

        return self.builder.gep(
            self.current_self_pointer,
            [zero, index],
            inbounds=True,
            name=f"self_{field_name}_ptr",
        )

    def generate_address(self, node):
        if isinstance(node, IdentifierNode):
            # 1. local / parameter
            local = self.lookup_local_variable(
                node.name
            )

            if local is not None:
                return local.pointer

            # 2. implicit field
            if self.current_struct_name is not None:
                struct = self.semantic.structs[
                    self.current_struct_name
                ]

                if node.name in struct.fields:
                    return self.generate_implicit_field_address(
                        node.name
                    )

            # 3. global
            if node.name in self.global_variables:
                return self.global_variables[
                    node.name
                ].pointer

            raise RuntimeError(
                f"internal compiler error: "
                f"cannot find '{node.name}'"
            )

        if isinstance(node, FieldAccessNode):
            return self.generate_field_address(node)

        raise RuntimeError(
            "internal compiler error: expression has no address"
        )

    def generate_receiver_pointer(self, node):
        if isinstance(
            node,
            (IdentifierNode, FieldAccessNode),
        ):
            return self.generate_address(node)

        # Non-addressable object expression:
        # materialize it into temporary storage.
        value = self.generate_expression(node)

        object_type = self.semantic.type_of(node)

        temp = self.create_entry_alloca(
            self.llvm_type(object_type),
            "receiver_temp",
        )

        self.builder.store(
            value,
            temp,
        )

        return temp

    def generate_member_call(self, node):
        object_type = self.semantic.type_of(
            node.object
        )

        llvm_function = self.member_functions[
            (object_type, node.method_name)
        ]

        method_symbol = self.semantic.structs[
            object_type
        ].methods[node.method_name]

        receiver = self.generate_receiver_pointer(
            node.object
        )

        arguments = [receiver]

        for argument_node, expected_type in zip(
            node.arguments,
            method_symbol.parameter_types,
        ):
            value = self.generate_expression(
                argument_node
            )

            actual_type = self.semantic.type_of(
                argument_node
            )

            value = self.widen_value(
                value,
                actual_type,
                expected_type,
            )

            arguments.append(value)

        return self.builder.call(
            llvm_function,
            arguments,
            name=(
                f"call_{object_type}_"
                f"{node.method_name}"
            ),
        )

    def generate_implicit_member_call(self, node):
        struct_name = self.current_struct_name

        method_symbol = self.semantic.structs[
            struct_name
        ].methods[node.name]

        llvm_function = self.member_functions[
            (struct_name, node.name)
        ]

        arguments = [
            self.current_self_pointer
        ]

        for argument_node, expected_type in zip(
            node.arguments,
            method_symbol.parameter_types,
        ):
            value = self.generate_expression(
                argument_node
            )

            actual_type = self.semantic.type_of(
                argument_node
            )

            value = self.widen_value(
                value,
                actual_type,
                expected_type,
            )

            arguments.append(value)

        return self.builder.call(
            llvm_function,
            arguments,
            name=f"call_self_{node.name}",
        )

    def string_pointer(self, global_string):
        return self.builder.bitcast(
            global_string,
            self.i8.as_pointer(),
        )

    def generate_read(self, node):
        slot = self.create_entry_alloca(
            self.i32,
            "read_value",
        )

        format_pointer = self.string_pointer(
            self.fmt_read_i32
        )

        self.builder.call(
            self.scanf,
            [
                format_pointer,
                slot,
            ],
        )

        return self.builder.load(
            slot,
            typ=self.i32,
            name="read_result",
        )

    def emit_primitive_value(
        self,
        value,
        type_name,
        newline,
    ):
        if type_name == "i32":
            fmt = (
                self.fmt_i32_line
                if newline
                else self.fmt_i32
            )

            self.builder.call(
                self.printf,
                [
                    self.string_pointer(fmt),
                    value,
                ],
            )

            return

        if type_name == "i64":
            fmt = (
                self.fmt_i64_line
                if newline
                else self.fmt_i64
            )

            self.builder.call(
                self.printf,
                [
                    self.string_pointer(fmt),
                    value,
                ],
            )

            return

        if type_name == "bool":
            true_ptr = self.string_pointer(
                self.true_string
            )

            false_ptr = self.string_pointer(
                self.false_string
            )

            selected = self.builder.select(
                value,
                true_ptr,
                false_ptr,
                name="bool_text",
            )

            fmt = (
                self.fmt_string_line
                if newline
                else self.fmt_string
            )

            self.builder.call(
                self.printf,
                [
                    self.string_pointer(fmt),
                    selected,
                ],
            )

            return

        raise RuntimeError(
            f"cannot print primitive type '{type_name}'"
        )

    def generate_print_string(self, node):
        global_string = self.create_global_string(
            node.value
        )

        self.builder.call(
            self.printf,
            [
                self.string_pointer(
                    self.fmt_string_line
                ),
                self.string_pointer(
                    global_string
                ),
            ],
        )

    def generate_print(self, node):
        if isinstance(
            node.value,
            StringLiteralNode,
        ):
            self.generate_print_string(
                node.value
            )
            return

        type_name = self.semantic.type_of(
            node.value
        )

        if type_name in (
            "i32",
            "i64",
            "bool",
        ):
            value = self.generate_expression(
                node.value
            )

            self.emit_primitive_value(
                value,
                type_name,
                newline=True,
            )

            return

        if type_name in self.struct_types:
            pointer = self.generate_receiver_pointer(
                node.value
            )

            self.generate_print_object(
                pointer,
                type_name,
                newline=True,
            )

            return

        raise RuntimeError(
            f"cannot print '{type_name}'"
        )

    def emit_text(self, text):
        string = self.create_global_string(text)

        self.builder.call(
            self.printf,
            [
                self.string_pointer(
                    self.fmt_string
                ),
                self.string_pointer(string),
            ],
        )

    def generate_print_object(
        self,
        object_pointer,
        struct_name,
        newline,
    ):
        struct_symbol = self.semantic.structs[
            struct_name
        ]

        struct_type = self.struct_types[
            struct_name
        ]

        fields = sorted(
            struct_symbol.fields.values(),
            key=lambda field: field.index,
        )

        # Point{
        self.emit_text(
            f"{struct_name}{{"
        )

        for position, field in enumerate(fields):
            if position > 0:
                self.emit_text(", ")

            # x:
            self.emit_text(
                f"{field.name}: "
            )

            field_pointer = self.builder.gep(
                object_pointer,
                [
                    ir.Constant(self.i32, 0),
                    ir.Constant(
                        self.i32,
                        field.index,
                    ),
                ],
                inbounds=True,
                name=f"print_{field.name}_ptr",
            )

            if field.type_name in (
                "i32",
                "i64",
                "bool",
            ):
                field_value = self.builder.load(
                    field_pointer,
                    typ=self.llvm_type(
                        field.type_name
                    ),
                    name=f"print_{field.name}",
                )

                self.emit_primitive_value(
                    field_value,
                    field.type_name,
                    newline=False,
                )

            elif field.type_name in self.struct_types:
                self.generate_print_object(
                    field_pointer,
                    field.type_name,
                    newline=False,
                )

        if newline:
            self.emit_text("}\n")
        else:
            self.emit_text("}")


def main():
    if len(sys.argv) != 3:
        print(
            "usage: python3 compiler.py --ast input.txt\n"
            "       python3 compiler.py input.txt output.ll",
            file=sys.stderr,
        )
        sys.exit(1)

    ast_mode = sys.argv[1] == "--ast"
    input_path = sys.argv[2] if ast_mode else sys.argv[1]
    try:
        with open(input_path, "rb") as source_file:
            source = source_file.read()
    except OSError as error:
        compilation_error(1, 1, f"cannot read input: {error}")

    program = Parser(Lexer(source).tokenize()).parse_program()
    if ast_mode:
        print(program.dump())
        return

    semantic = SemanticAnalyzer()
    semantic.analyze(program)
    try:
        generator = CodeGenerator(semantic)
    except ImportError:
        compilation_error(1, 1, "LLVM generation requires llvmlite; install requirements.txt")
    module_text = generator.generate(program)
    try:
        with open(sys.argv[2], "w", encoding="utf-8") as output_file:
            output_file.write(module_text)
    except OSError as error:
        compilation_error(1, 1, f"cannot write output: {error}")


if __name__ == "__main__":
    main()
