import contextlib
import io
import unittest

from compiler import (
    IdentifierNode, Lexer, MemberFunctionSymbol, Parser, SemanticAnalyzer,
    VariableSymbol,
)


def program(source):
    return Parser(Lexer(source.encode('utf-8')).tokenize()).parse_program()


def analyze(source):
    analyzer = SemanticAnalyzer()
    analyzer.analyze(program(source))
    return analyzer


class ObjectSemanticTests(unittest.TestCase):
    def test_object_creation_access_and_assignment(self):
        analyzer = analyze('''mewi Point { var 🐱 x var 🐱 y }
var Point p meow Point{10, 20}
var 🐱 result meow p.x
p.x meow 50
result meow p.y
🐾(p)
''')
        self.assertEqual(analyzer.globals['p'].type_name, 'Point')
        self.assertEqual(analyzer.globals['result'].type_name, 'i32')

    def test_nested_objects_and_mutable_chain(self):
        analyzer = analyze('''mewi Circle { var Point center var 🐱 radius }
mewi Point { var 🐱 x var 🐱 y }
var Circle c meow Circle{Point{10, 20}, 5}
var 🐱 result meow c.center.x
c.center.x meow 50
c.center meow Point{1, 2}
c meow Circle{Point{3, 4}, 6}
🐾(c)
''')
        self.assertEqual(analyzer.globals['c'].type_name, 'Circle')

    def test_objects_in_function_signatures_and_returns(self):
        analyzer = analyze('''mewi Point { var 🐱 x }
murr make(🐱 x) kss Point { mi Point{x} }
murr copy(Point p) kss Point { mi p }
let Point p meow copy(make(1))
🐾(p.x)
''')
        self.assertEqual(analyzer.globals['p'].type_name, 'Point')

    def test_errors(self):
        point = 'mewi Point { var 🐱 x var 🐱 y }\n'
        cases = [
            ('var 🐱 x meow Banana{}', "unknown structure 'Banana'"),
            (point + 'var Point p meow Point{1}', "expects 2 values, got 1"),
            (point + 'var Point p meow Point{1, 2, 3}', "expects 2 values, got 3"),
            (point + 'var Point p meow Point{true, 2}', "field 'x' of structure 'Point' requires type 'i32', got 'bool'"),
            (point + 'var Point p meow Point{1, 2} 🐾(p.z)', "structure 'Point' has no field 'z'"),
            ('var 🐱 n meow 1 🐾(n.x)', "type 'i32' has no fields"),
            (point + 'let Point p meow Point{1, 2} p.x meow 3', "cannot assign to constant 'p'"),
            ('mewi Point { let 🐱 x } var Point p meow Point{1} p.x meow 2', "cannot assign through constant field 'x'"),
            ('mewi Point { var 🐱 x } mewi Circle { let Point center } var Circle c meow Circle{Point{1}} c.center.x meow 2', "cannot assign through constant field 'center'"),
            (point + 'var Point p meow Point{1, 2} p.x meow true', "cannot assign value of type 'bool' to target of type 'i32'"),
            (point + 'var Point p meow Point{1, 2} p.z meow 3', "structure 'Point' has no field 'z'"),
            ('var 🐱 n meow 1 n.x meow 2', "type 'i32' has no fields"),
            ('missing meow 1', "unknown name 'missing'"),
            ('let 🐱 x meow 1 x meow 2', "cannot assign to constant 'x'"),
            ('murr f(🐱 x) kss 🐱 { x meow 1 mi x }', "cannot assign to constant 'x'"),
        ]
        for source, message in cases:
            with self.subTest(source=source):
                error = io.StringIO()
                with contextlib.redirect_stderr(error), self.assertRaises(SystemExit) as raised:
                    analyze(source)
                self.assertEqual(raised.exception.code, 1)
                self.assertEqual(len(error.getvalue().splitlines()), 1)
                self.assertRegex(error.getvalue(), r'^compilation error: line [1-9]\d*:[1-9]\d*: ')
                self.assertIn(message, error.getvalue())

    def test_mutation_marker_distinguishes_fields_from_locals(self):
        analyzer = SemanticAnalyzer()
        analyzer.collect_declarations(program('mewi P { var 🐱 x }'))
        analyzer.current_struct = 'P'
        method = MemberFunctionSymbol('setX', [], 'i32', False)
        analyzer.current_function = method
        analyzer.push_scope()
        analyzer.scopes[-1]['x'] = VariableSymbol('x', 'i32', True)
        analyzer.check_assignment_target(IdentifierNode(1, 1, 'x'))
        self.assertFalse(method.mutating)
        analyzer.pop_scope()
        analyzer.check_assignment_target(IdentifierNode(1, 1, 'x'))
        self.assertTrue(method.mutating)


if __name__ == '__main__':
    unittest.main()
