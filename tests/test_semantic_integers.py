import contextlib
import io
import unittest

from compiler import I32_MAX, I32_MIN, I64_MAX, I64_MIN, Lexer, Parser, SemanticAnalyzer


def parse(source):
    return Parser(Lexer(source.encode('utf-8')).tokenize()).parse_program()


def analyze(source):
    program = parse(source)
    analyzer = SemanticAnalyzer()
    analyzer.analyze(program)
    return analyzer, program


class IntegerSemanticTests(unittest.TestCase):
    def test_narrowest_literal_type_at_boundaries(self):
        for value, expected in [
            (0, 'i32'), (I32_MIN, 'i32'), (I32_MAX, 'i32'),
            (I32_MIN - 1, 'i64'), (I32_MAX + 1, 'i64'),
            (I64_MIN, 'i64'), (I64_MAX, 'i64'),
        ]:
            with self.subTest(value=value):
                analyzer, program = analyze(f'🐾({value})')
                expression = program.statements[0].value
                self.assertEqual(analyzer.type_of(expression), expected)
                if value < 0:
                    self.assertEqual(analyzer.signed_literals[id(expression)], value)
                    self.assertEqual(analyzer.type_of(expression.operand), expected)

    def test_global_local_and_assignment_widening(self):
        analyzer, program = analyze('''var 🐱 small meow -5
var 🐈 big meow small
big meow 10
murr f() kss 🐈 { var 🐈 local meow small mi local }
''')
        self.assertEqual(analyzer.globals['big'].type_name, 'i64')
        source = program.statements[1].value
        self.assertEqual(analyzer.expression_types[id(source)], 'i32')
        self.assertEqual(analyzer.widenings[id(source)], 'i64')

    def test_arithmetic_width_is_not_forced_by_destination(self):
        analyzer, program = analyze('''var 🐱 a meow 1
var 🐈 b meow 3000000000
var 🐈 mixed meow a + b
var 🐈 reverse meow b * a
var 🐈 narrowCalculation meow a + 1
''')
        mixed = program.statements[2].value
        narrow = program.statements[4].value
        self.assertEqual(analyzer.expression_types[id(mixed)], 'i64')
        self.assertEqual(analyzer.widenings[id(mixed.left)], 'i64')
        self.assertEqual(analyzer.expression_types[id(narrow)], 'i32')
        self.assertEqual(analyzer.widenings[id(narrow)], 'i64')

    def test_mixed_comparisons(self):
        analyzer, _ = analyze('''var 🐱 a meow 1
var 🐈 b meow 3000000000
var 😺 same meow a meowmeow b
var 😺 different meow b woem a
var 😺 booleans meow true meowmeow false
''')
        self.assertEqual(analyzer.globals['same'].type_name, 'bool')

    def test_object_comparison_is_not_supported(self):
        for operator in ['meowmeow', 'woem']:
            with self.subTest(operator=operator):
                error = io.StringIO()
                with contextlib.redirect_stderr(error), self.assertRaises(SystemExit):
                    analyze('mewi P { var 🐱 x } var P p meow P{1} '
                            f'var 😺 same meow p {operator} p')
                self.assertIn("cannot compare 'P' with 'P'", error.getvalue())

    def test_codegen_type_lookup_keeps_operand_and_result_widths(self):
        analyzer, program = analyze('var 🐈 b meow 3000000000 var 🐈 c meow 1 + b')
        expression = program.statements[1].value
        self.assertEqual(analyzer.type_of(expression.left), 'i32')
        self.assertEqual(analyzer.type_of(expression.right), 'i64')
        self.assertEqual(analyzer.type_of(expression), 'i64')
        self.assertEqual(analyzer.widenings[id(expression.left)], 'i64')

    def test_widening_in_calls_returns_fields_and_methods(self):
        analyzer, _ = analyze('''murr widen(🐈 value) kss 🐈 { mi value }
murr literal() kss 🐈 { mi 1 }
mewi Wide {
    var 🐈 x
    murr set(🐈 value) kss 🐈 { x meow value mi x }
    murr implicit() kss 🐈 { mi set(1) }
    murr smallReturn() kss 🐈 { mi 2 }
}
var Wide w meow Wide{1}
w.x meow 2
w.set(3)
var 🐈 result meow widen(4)
''')
        self.assertEqual(analyzer.globals['result'].type_name, 'i64')
        self.assertTrue(analyzer.structs['Wide'].methods['implicit'].mutating)

    def test_out_of_range_and_narrowing_rejected(self):
        for source, message in [
            (f'🐾({I64_MAX + 1})', 'does not fit in i64'),
            (f'🐾({I64_MIN - 1})', 'does not fit in i64'),
            ('var 🐱 x meow 3000000000', "value of type 'i64'"),
            ('var 🐈 big meow 1 var 🐱 small meow big', "value of type 'i64'"),
            ('var 🐱 x meow 1 x meow 3000000000', "target of type 'i32'"),
            ('var 🐱 x meow 1 + 3000000000', "value of type 'i64'"),
            ('murr f(🐱 x) kss 🐱 { mi x } f(3000000000)', "must have type 'i32', got 'i64'"),
            ('murr f() kss 🐱 { mi 3000000000 }', "must return 'i32', got 'i64'"),
            ('mewi P { var 🐱 x } var P p meow P{3000000000}', "requires type 'i32', got 'i64'"),
            ('mewi P { var 🐱 x murr set(🐱 n) kss 🐱 { mi n } } var P p meow P{1} p.set(3000000000)', "must have type 'i32', got 'i64'"),
            ('mewi P { var 🐱 x murr f() kss 🐱 { mi set(3000000000) } murr set(🐱 n) kss 🐱 { mi n } }', "must have type 'i32', got 'i64'"),
            ('var 🐈 x meow true', "value of type 'bool'"),
            ('var 😺 same meow true meowmeow 3000000000', "cannot compare 'bool' with 'i64'"),
        ]:
            with self.subTest(source=source):
                error = io.StringIO()
                with contextlib.redirect_stderr(error), self.assertRaises(SystemExit):
                    analyze(source)
                self.assertEqual(len(error.getvalue().splitlines()), 1)
                self.assertIn(message, error.getvalue())

    def test_runtime_arithmetic_is_not_folded_by_semantics(self):
        analyze(f'var 🐱 x meow {I32_MAX} x meow x + 1')
        analyze(f'var 🐈 x meow {I64_MIN} x meow -x')

    def test_huge_literals_do_not_raise_python_tracebacks(self):
        error = io.StringIO()
        with contextlib.redirect_stderr(error), self.assertRaises(SystemExit):
            analyze('🐾(' + '9' * 5000 + ')')
        self.assertIn('does not fit in i64', error.getvalue())
        self.assertEqual(len(error.getvalue().splitlines()), 1)
        analyze('var 🐱 x meow ' + '0' * 5000 + '1')

    def test_division_is_not_in_the_language(self):
        error = io.StringIO()
        with contextlib.redirect_stderr(error), self.assertRaises(SystemExit):
            parse('var 🐱 x meow 4 / 2')
        self.assertIn('unexpected character /', error.getvalue())


if __name__ == '__main__':
    unittest.main()
