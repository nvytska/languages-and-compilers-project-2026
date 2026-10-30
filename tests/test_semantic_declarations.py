import contextlib
import io
import unittest

from compiler import Lexer, Parser, SemanticAnalyzer


def collect(source):
    program = Parser(Lexer(source.encode('utf-8')).tokenize()).parse_program()
    analyzer = SemanticAnalyzer()
    analyzer.collect_declarations(program)
    return analyzer


class DeclarationTests(unittest.TestCase):
    def test_metadata_and_forward_types(self):
        analyzer = collect('''mewi Circle { var Point center }
murr copy(Point p) kss Point { mi p }
mewi Point {
    var 🐱 x
    let 🐱 y
    murr getX() kss 🐱 { mi x }
    murr setX(🐱 value) kss 🐱 { x meow value mi x }
}
murr add(🐱 a, 🐱 b) kss 🐱 { mi a + b }
''')
        self.assertEqual(analyzer.structs['Circle'].fields['center'].type_name, 'Point')
        point = analyzer.structs['Point']
        self.assertEqual([(f.name, f.type_name, f.mutable, f.index) for f in point.fields.values()],
                         [('x', 'i32', True, 0), ('y', 'i32', False, 1)])
        self.assertEqual(point.methods['getX'].parameter_types, [])
        self.assertEqual(point.methods['getX'].result_type, 'i32')
        self.assertEqual(point.methods['setX'].parameter_types, ['i32'])
        self.assertFalse(point.methods['setX'].mutating)  # Body analysis comes later.
        self.assertEqual(analyzer.functions['add'].parameter_types, ['i32', 'i32'])
        self.assertEqual(analyzer.functions['copy'].result_type, 'Point')
        self.assertEqual(analyzer.globals, {})

    def test_bodies_and_variable_declarations_are_not_checked(self):
        analyzer = collect('''murr foo() kss 🐱 { mi bar(true) }
murr bar() kss 🐱 { mi unknown }
var Banana value meow missing()
''')
        self.assertEqual(set(analyzer.functions), {'foo', 'bar'})
        self.assertEqual(analyzer.globals, {})

    def test_declaration_errors(self):
        cases = [
            ('mewi P { var 🐱 x }\nmewi P { var 🐱 y }',
             "line 2:1: structure 'P' is already declared"),
            ('murr f() kss 🐱 { mi 1 }\nmurr f() kss 🐱 { mi 2 }',
             "line 2:1: function 'f' is already declared"),
            ('mewi P {\nvar 🐱 x\nlet 🐱 x\n}',
             "line 3:1: field 'x' is already declared in structure 'P'"),
            ('mewi P { var 🐱 x\nmurr f() kss 🐱 { mi 1 }\nmurr f() kss 🐱 { mi 2 } }',
             "line 3:1: member function 'f' is already declared in structure 'P'"),
            ('murr f(Banana x) kss 🐱 { mi 1 }',
             "line 1:8: unknown type 'Banana'"),
            ('murr f() kss Banana { mi 1 }',
             "line 1:1: unknown type 'Banana'"),
            ('mewi P {\nvar Banana x\n}',
             "line 2:1: unknown type 'Banana'"),
            ('mewi P { var 🐱 x\nmurr f(Banana value) kss 🐱 { mi 1 } }',
             "line 2:8: unknown type 'Banana'"),
            ('mewi P { var 🐱 x\nmurr f() kss Banana { mi 1 } }',
             "line 2:1: unknown type 'Banana'"),
            ('murr f(🐱 x, 🐱 x) kss 🐱 { mi 1 }',
             "line 1:13: parameter 'x' is already declared"),
            ('mewi P { var 🐱 x\nmurr f(🐱 a, 🐱 a) kss 🐱 { mi 1 } }',
             "line 2:13: parameter 'a' is already declared"),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                error = io.StringIO()
                with contextlib.redirect_stderr(error), self.assertRaises(SystemExit) as raised:
                    collect(source)
                self.assertEqual(raised.exception.code, 1)
                self.assertEqual(error.getvalue(), 'compilation error: ' + expected + '\n')

    def test_structs_keep_independent_member_tables(self):
        analyzer = collect('''mewi A { var 🐱 x murr get() kss 🐱 { mi x } }
mewi B { let 🐈 x murr get() kss 🐈 { mi x } }
''')
        self.assertEqual(analyzer.structs['A'].fields['x'].type_name, 'i32')
        self.assertEqual(analyzer.structs['B'].fields['x'].type_name, 'i64')
        self.assertEqual(analyzer.structs['B'].methods['get'].result_type, 'i64')

    def test_recursive_value_layouts_are_rejected_before_llvm(self):
        for source in ['mewi P { var P self }',
                       'mewi A { var B b } mewi B { var A a }']:
            with self.subTest(source=source):
                error = io.StringIO()
                with contextlib.redirect_stderr(error), self.assertRaises(SystemExit):
                    collect(source)
                self.assertEqual(len(error.getvalue().splitlines()), 1)
                self.assertIn('recursive structure fields have no finite size', error.getvalue())


if __name__ == '__main__':
    unittest.main()
