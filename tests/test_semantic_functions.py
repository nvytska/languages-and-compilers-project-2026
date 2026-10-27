import contextlib
import io
import unittest

from compiler import Lexer, Parser, SemanticAnalyzer


def program(source):
    return Parser(Lexer(source.encode('utf-8')).tokenize()).parse_program()


def analyze(source):
    analyzer = SemanticAnalyzer()
    analyzer.analyze(program(source))
    return analyzer


class FunctionSemanticTests(unittest.TestCase):
    def test_forward_and_nested_calls(self):
        analyzer = analyze('''murr twice(🐱 value) kss 🐱 { mi add(value, value) }
murr add(🐱 a, 🐱 b) kss 🐱 { mi a + b }
var 🐱 result meow twice(add(2, 3))
🐾(result)
🐾(true)
🐾("hello")
''')
        self.assertEqual(analyzer.globals['result'].type_name, 'i32')
        self.assertEqual(analyzer.scopes, [])
        self.assertIsNone(analyzer.current_function)

    def test_recursion_and_complete_returns(self):
        analyze('''murr count(🐱 n) kss 🐱 {
    if n meowmeow 0 { mi 0 } else { mi count(n - 1) }
}
murr finish(😺 condition) kss 🐱 {
    if condition { mi 1 }
    mi 2
}
murr mutualA() kss 🐱 { mi mutualB() }
murr mutualB() kss 🐱 { mi mutualA() }
''')

    def test_scope_shadowing_and_global_visibility(self):
        analyzer = analyze('''var 😺 x meow true
murr f(🐱 x) kss 🐱 {
    if true { var 😺 x meow false 🐾(x) } else { var 🐱 x meow 2 }
    mi x
}
murr globalValue() kss 😺 { mi x }
if true { var 🐱 local meow 1 }
''')
        self.assertEqual(set(analyzer.globals), {'x'})
        self.assertEqual(analyzer.globals['x'].type_name, 'bool')

    def test_errors_and_context_cleanup(self):
        declaration = 'murr add(🐱 a, 🐱 b) kss 🐱 { mi a + b }\n'
        cases = [
            (declaration + 'add(1)', "expects 2 arguments, got 1"),
            (declaration + 'add(1, 2, 3)', "expects 2 arguments, got 3"),
            (declaration + 'add(true, 2)', "argument 1 of function 'add' must have type 'i32', got 'bool'"),
            ('missing()', "unknown function 'missing'"),
            ('murr bad() kss 🐱 { mi true }', "function must return 'i32', got 'bool'"),
            ('mi 1', 'mi may only be used inside a function'),
            ('murr bad() kss 🐱 { var 🐱 x meow 1 }', "function 'bad' may finish without mi"),
            ('murr bad(😺 c) kss 🐱 { if c { mi 1 } }', "may finish without mi"),
            ('if 1 { 🐾(1) }', "if condition must be bool, got 'i32'"),
            ('if true { var 🐱 x meow 1 } 🐾(x)', "unknown name 'x'"),
            ('if true { var 🐱 x meow 1 } else { 🐾(x) }', "unknown name 'x'"),
            ('murr bad(🐱 x) kss 🐱 { var 🐱 x meow 1 mi x }', "already declared in this scope"),
            ('murr f() kss 🐱 { mi later } var 🐱 later meow 1', "unknown name 'later'"),
        ]
        for source, message in cases:
            with self.subTest(source=source):
                analyzer = SemanticAnalyzer()
                error = io.StringIO()
                with contextlib.redirect_stderr(error), self.assertRaises(SystemExit) as raised:
                    analyzer.analyze(program(source))
                self.assertEqual(raised.exception.code, 1)
                self.assertEqual(len(error.getvalue().splitlines()), 1)
                self.assertRegex(error.getvalue(), r'^compilation error: line [1-9]\d*:[1-9]\d*: ')
                self.assertIn(message, error.getvalue())
                self.assertEqual(analyzer.scopes, [])
                self.assertIsNone(analyzer.current_function)
                self.assertIsNone(analyzer.current_struct)

    def test_parameters_are_immutable(self):
        class InspectingAnalyzer(SemanticAnalyzer):
            def check_return(self, node):
                self.parameter_mutability = self.lookup_variable('x').mutable
                super().check_return(node)

        analyzer = InspectingAnalyzer()
        analyzer.analyze(program('murr identity(🐱 x) kss 🐱 { mi x }'))
        self.assertFalse(analyzer.parameter_mutability)


if __name__ == '__main__':
    unittest.main()
