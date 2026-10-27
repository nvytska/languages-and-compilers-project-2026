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


class TokenKind(Enum):
    VAR = auto()
    LET = auto()
    IF = auto()
    ELSE = auto()
    TRUE = auto()
    FALSE = auto()
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

        if self.current_byte() == ord("-"):
            self.advance()

        while self.is_digit(self.current_byte()):
            self.advance()

        text = self.source[start:self.pos].decode("utf-8")

        return Token(TokenKind.INTEGER, text, line, column)

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

        if byte == ord("-"):
            next_pos = self.pos + 1

            if (
                next_pos < len(self.source)
                and self.is_digit(self.source[next_pos])
            ):
                return self.lex_integer()

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
    name: str
    value: ExprNode

    def dump(self, indent=0):
        pad = "  " * indent
        return "\n".join([
            f"{pad}Assignment",
            f"{pad}  name: {self.name}",
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


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

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

    def parse_program(self):
        statements = []
        start = self.peek()

        while self.peek().kind != TokenKind.EOF:
            statements.append(self.parse_statement())

        self.eat(TokenKind.EOF)

        return ProgramNode(start.line, start.column, statements)

    def parse_statement(self):
        token = self.peek()

        if token.kind in (TokenKind.VAR, TokenKind.LET):
            return self.parse_variable_declaration()

        if token.kind == TokenKind.IDENTIFIER:
            return self.parse_assignment()

        if token.kind == TokenKind.IF:
            return self.parse_if_statement()

        compilation_error(
            token.line,
            token.column,
            f"unexpected token {token.text}",
        )

    def parse_variable_declaration(self):
        start = self.peek()

        if start.kind == TokenKind.VAR:
            self.eat(TokenKind.VAR)
            mutable = True
        else:
            self.eat(TokenKind.LET)
            mutable = False

        type_token = self.peek()

        if type_token.kind == TokenKind.TYPE_I32:
            self.eat(TokenKind.TYPE_I32)
            type_name = "i32"
        elif type_token.kind == TokenKind.TYPE_I64:
            self.eat(TokenKind.TYPE_I64)
            type_name = "i64"
        elif type_token.kind == TokenKind.TYPE_BOOL:
            self.eat(TokenKind.TYPE_BOOL)
            type_name = "bool"
        else:
            compilation_error(
                type_token.line,
                type_token.column,
                "expected type",
            )

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

    def parse_assignment(self):
        name_token = self.eat(TokenKind.IDENTIFIER)
        self.eat(TokenKind.ASSIGN)
        value = self.parse_expression()

        return AssignmentNode(
            name_token.line,
            name_token.column,
            name_token.text,
            value,
        )

    def parse_if_statement(self):
        if_token = self.eat(TokenKind.IF)
        condition = self.parse_expression()
        self.eat(TokenKind.LBRACE)
        then_body = []

        if self.peek().kind == TokenKind.RBRACE:
            token = self.peek()
            compilation_error(
                token.line,
                token.column,
                "if block must contain at least one statement",
            )

        while self.peek().kind != TokenKind.RBRACE:
            if self.peek().kind == TokenKind.EOF:
                token = self.peek()
                compilation_error(
                    token.line,
                    token.column,
                    "expected }",
                )

            then_body.append(self.parse_statement())

        self.eat(TokenKind.RBRACE)
        else_body = None

        if self.peek().kind == TokenKind.ELSE:
            self.eat(TokenKind.ELSE)
            self.eat(TokenKind.LBRACE)
            else_body = []

            if self.peek().kind == TokenKind.RBRACE:
                token = self.peek()
                compilation_error(
                    token.line,
                    token.column,
                    "else block must contain at least one statement",
                )

            while self.peek().kind != TokenKind.RBRACE:
                if self.peek().kind == TokenKind.EOF:
                    token = self.peek()
                    compilation_error(
                        token.line,
                        token.column,
                        "expected }",
                    )

                else_body.append(self.parse_statement())

            self.eat(TokenKind.RBRACE)

        return IfNode(
            if_token.line,
            if_token.column,
            condition,
            then_body,
            else_body,
        )

    def parse_expression(self):
        left = self.parse_primary()
        token = self.peek()

        if token.kind == TokenKind.EQUAL:
            op_token = self.eat(TokenKind.EQUAL)
            right = self.parse_primary()
            return ComparisonNode(
                op_token.line,
                op_token.column,
                "meowmeow",
                left,
                right,
            )

        if token.kind == TokenKind.NOT_EQUAL:
            op_token = self.eat(TokenKind.NOT_EQUAL)
            right = self.parse_primary()
            return ComparisonNode(
                op_token.line,
                op_token.column,
                "woem",
                left,
                right,
            )

        return left

    def parse_primary(self):
        token = self.peek()

        if token.kind == TokenKind.INTEGER:
            token = self.eat(TokenKind.INTEGER)
            return IntegerLiteralNode(
                token.line,
                token.column,
                int(token.text),
            )

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

        if token.kind == TokenKind.IDENTIFIER:
            token = self.eat(TokenKind.IDENTIFIER)
            return IdentifierNode(
                token.line,
                token.column,
                token.text,
            )

        compilation_error(
            token.line,
            token.column,
            f"expected expression, got {token.kind.name}",
        )


def main():
    if len(sys.argv) != 3 or sys.argv[1] != "--ast":
        print(
            "usage: python3 compiler.py --ast input.txt",
            file=sys.stderr,
        )
        sys.exit(1)

    input_path = sys.argv[2]

    try:
        with open(input_path, "rb") as f:
            source = f.read()
    except OSError as error:
        print(
            f"error: cannot read {input_path}: {error}",
            file=sys.stderr,
        )
        sys.exit(1)

    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    program = parser.parse_program()
    print(program.dump())


if __name__ == "__main__":
    main()
