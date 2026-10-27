import contextlib
import io
import unittest

from compiler import (
    FieldSymbol, IdentifierNode, Lexer, Parser, SemanticAnalyzer, StructSymbol,
    VariableSymbol,
)


def analyze(source):
    program = Parser(Lexer(source.encode('utf-8')).tokenize()).parse_program()
    analyzer = SemanticAnalyzer()
    analyzer.analyze(program)
    return analyzer


class ExpressionSemanticTests(unittest.TestCase):
    def test_variables_arithmetic_comparisons_and_read(self):
        analyzer = analyze('''var 🐱 x meow 5
var 🐱 y meow 10
let 🐱 result meow -(x + y * 2)
var 😺 same meow result meowmeow x
var 😺 opposite meow true woem false
var 🐱 input meow 📚()
''')
        self.assertEqual(analyzer.globals['result'].type_name, 'i32')
        self.assertFalse(analyzer.globals['result'].mutable)
        self.assertEqual(analyzer.globals['same'].type_name, 'bool')
        self.assertEqual(analyzer.globals['input'].type_name, 'i32')
        self.assertEqual(analyzer.scopes, [])

    def test_rejected_programs(self):
        cases = [
            ('var 🐱 x meow true', "cannot initialize 'x'"),
            ('var 🐱 x meow x', "unknown name 'x'"),
            ('var 🐱 x meow y var 🐱 y meow 1', "unknown name 'y'"),
            ('var 🐱 x meow 1 var 🐱 x meow 2', "global variable 'x' is already declared"),
            ('var Banana x meow 1', "unknown type 'Banana'"),
            ('var 🐱 x meow true + 1', "requires integer operands"),
            ('var 🐱 x meow true + false', "requires integer operands"),
            ('var 😺 x meow 5 meowmeow true', "cannot compare 'i32' with 'bool'"),
            ('var 🐱 x meow -true', "unary '-' requires an integer operand"),
        ]
        for source, message in cases:
            with self.subTest(source=source):
                error = io.StringIO()
                analyzer = SemanticAnalyzer()
                program = Parser(Lexer(source.encode('utf-8')).tokenize()).parse_program()
                with contextlib.redirect_stderr(error), self.assertRaises(SystemExit) as raised:
                    analyzer.analyze(program)
                self.assertEqual(raised.exception.code, 1)
                self.assertEqual(len(error.getvalue().splitlines()), 1)
                self.assertRegex(error.getvalue(), r'^compilation error: line [1-9]\d*:[1-9]\d*: ')
                self.assertIn(message, error.getvalue())
                self.assertEqual(analyzer.scopes, [])

    def test_lookup_order_and_nested_scopes(self):
        analyzer = SemanticAnalyzer()
        global_x = VariableSymbol('x', 'i64', False)
        field_x = FieldSymbol('x', 'bool', True, 0)
        local_x = VariableSymbol('x', 'i32', True)
        analyzer.globals['x'] = global_x
        analyzer.structs['P'] = StructSymbol('P', {'x': field_x}, {})
        self.assertIs(analyzer.lookup_variable('x'), global_x)
        analyzer.current_struct = 'P'
        self.assertIs(analyzer.lookup_variable('x'), field_x)
        analyzer.push_scope()
        analyzer.scopes[-1]['x'] = local_x
        analyzer.push_scope()
        self.assertIs(analyzer.lookup_variable('x'), local_x)
        analyzer.scopes[-1]['x'] = VariableSymbol('x', 'i64', True)
        self.assertEqual(analyzer.check_identifier(IdentifierNode(1, 1, 'x')), 'i64')
        analyzer.pop_scope()
        self.assertIs(analyzer.lookup_variable('x'), local_x)
        analyzer.pop_scope()
        self.assertIs(analyzer.lookup_variable('x'), field_x)
        self.assertIsNone(analyzer.lookup_variable('missing'))

    def test_i64_operands_keep_their_width(self):
        analyzer = SemanticAnalyzer()
        analyzer.globals['a'] = VariableSymbol('a', 'i64', True)
        analyzer.globals['b'] = VariableSymbol('b', 'i64', True)
        program = Parser(Lexer('var 🐈 result meow a + b'.encode('utf-8')).tokenize()).parse_program()
        analyzer.check_program(program)
        self.assertEqual(analyzer.globals['result'].type_name, 'i64')


if __name__ == '__main__':
    unittest.main()
