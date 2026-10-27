import contextlib
import io
import unittest

from compiler import Lexer, Parser, SemanticAnalyzer


POINT = '''mewi Point {
    var 🐱 x
    murr getX() kss 🐱 { mi x }
    murr setX(🐱 value) kss 🐱 { x meow value mi x }
}
'''


def analyze(source, analyzer=None):
    analyzer = analyzer or SemanticAnalyzer()
    analyzer.analyze(Parser(Lexer(source.encode('utf-8')).tokenize()).parse_program())
    return analyzer


class MemberSemanticTests(unittest.TestCase):
    def test_readonly_const_and_mutable_setter(self):
        analyzer = analyze(POINT + '''let Point constant meow Point{1}
var Point mutable meow Point{2}
🐾(constant.getX())
mutable.setX(3)
''')
        methods = analyzer.structs['Point'].methods
        self.assertFalse(methods['getX'].mutating)
        self.assertTrue(methods['setX'].mutating)

    def test_lookup_precedence_and_global_fallback(self):
        analyze('''var 😺 x meow true
var 🐱 globalValue meow 5
murr getX() kss 😺 { mi true }
mewi Point {
    var 🐱 x
    murr getX() kss 🐱 { mi x }
    murr fromParameter(😺 x) kss 😺 { mi x }
    murr fromLocal() kss 😺 { let 😺 x meow false mi x }
    murr fromGlobal() kss 🐱 { mi globalValue }
    murr twiceX() kss 🐱 { mi getX() + getX() }
}
''')

    def test_transitive_mutation_through_forward_and_recursive_calls(self):
        analyzer = analyze('''mewi P {
    var 🐱 x
    murr first() kss 🐱 { mi second() }
    murr second() kss 🐱 { mi third() }
    murr third() kss 🐱 { x meow 1 mi first() }
}
var P p meow P{1}
p.first()
''')
        self.assertTrue(all(m.mutating for m in analyzer.structs['P'].methods.values()))

    def test_mutation_through_nested_object_receiver(self):
        analyzer = analyze('''mewi Circle {
    var Point center
    murr update() kss 🐱 { mi center.setX(2) }
}
''' + POINT + 'var Circle c meow Circle{Point{1}} c.update()')
        self.assertTrue(analyzer.structs['Circle'].methods['update'].mutating)

    def test_local_object_mutation_does_not_mutate_current_object(self):
        analyzer = analyze(POINT + '''mewi Wrapper {
    var 🐱 x
    murr work() kss 🐱 { var Point p meow Point{1} mi p.setX(2) }
}
let Wrapper w meow Wrapper{0}
w.work()
''')
        self.assertFalse(analyzer.structs['Wrapper'].methods['work'].mutating)

    def test_errors(self):
        wrapper = '''mewi P {
    var 🐱 x
    murr wrapper() kss 🐱 { mi set() }
    murr set() kss 🐱 { x meow 1 mi x }
}
'''
        cases = [
            (POINT + 'let Point p meow Point{1} p.setX(2)', "cannot call mutating member function on constant 'p'"),
            (POINT + 'var Point p meow Point{1} p.fly()', "has no member function 'fly'"),
            (POINT + 'var Point p meow Point{1} p.setX()', 'expects 1 arguments, got 0'),
            (POINT + 'var Point p meow Point{1} p.setX(1, 2)', 'expects 1 arguments, got 2'),
            (POINT + 'var Point p meow Point{1} p.setX(true)', "argument 1 of member function 'setX' must have type 'i32', got 'bool'"),
            ('var 🐱 n meow 1 n.get()', "type 'i32' has no member functions"),
            (POINT + 'mewi C { let Point center } var C c meow C{Point{1}} c.center.setX(2)', "cannot assign through constant field 'center'"),
            (POINT + 'mewi C { var Point center } let C c meow C{Point{1}} c.center.setX(2)', "cannot assign to constant 'c'"),
            (POINT + '🐾(Point{1}.setX(2))', 'requires a mutable object'),
            (wrapper + 'let P p meow P{1} p.wrapper()', "cannot call mutating member function on constant 'p'"),
            ('mewi P { var 🐱 x murr bad() kss 🐱 { mi true } }', "function must return 'i32', got 'bool'"),
            ('mewi P { var 🐱 x murr bad() kss 🐱 { 🐾(x) } }', "member function 'bad' may finish without mi"),
            ('mewi P { var 🐱 x murr f() kss 🐱 { mi set(true) } murr set(🐱 n) kss 🐱 { mi n } }', "argument 1 of member function 'set'"),
            ('mewi P { var 🐱 x murr f() kss 🐱 { mi set() } murr set(🐱 n) kss 🐱 { mi n } }', 'expects 1 arguments, got 0'),
            ('mewi P { let 🐱 x murr set() kss 🐱 { x meow 1 mi x } }', "cannot assign to constant 'x'"),
        ]
        for source, message in cases:
            with self.subTest(source=source):
                analyzer = SemanticAnalyzer()
                error = io.StringIO()
                with contextlib.redirect_stderr(error), self.assertRaises(SystemExit) as raised:
                    analyze(source, analyzer)
                self.assertEqual(raised.exception.code, 1)
                self.assertEqual(len(error.getvalue().splitlines()), 1)
                self.assertIn(message, error.getvalue())
                self.assertEqual(analyzer.scopes, [])
                self.assertIsNone(analyzer.current_function)
                self.assertIsNone(analyzer.current_struct)


if __name__ == '__main__':
    unittest.main()
