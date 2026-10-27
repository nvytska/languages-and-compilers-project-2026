import contextlib
import io
import unittest

from compiler import (
    AssignmentNode, BinaryOpNode, CallNode, FieldAccessNode, IdentifierNode,
    Lexer, MemberCallNode, ObjectCreationNode, Parser, ReadNode, UnaryOpNode,
)


def parse(source):
    return Parser(Lexer(source.encode("utf-8")).tokenize()).parse_program()


class ParserTests(unittest.TestCase):
    def test_function_example(self):
        program = parse('''murr add(🐱 a, 🐱 b) kss 🐱 {
    mi a + b
}
var 🐱 result meow add(2, 3)
🐾(result)
''')
        function, declaration, printing = program.statements
        self.assertEqual(function.name, 'add')
        self.assertEqual([(p.type_name, p.name) for p in function.parameters],
                         [('i32', 'a'), ('i32', 'b')])
        self.assertEqual(function.result_type, 'i32')
        self.assertIsInstance(function.body[0].value, BinaryOpNode)
        self.assertIsInstance(declaration.value, CallNode)
        self.assertEqual([a.value for a in declaration.value.arguments], [2, 3])
        self.assertEqual(printing.value.name, 'result')

    def test_structure_example(self):
        program = parse('''mewi Point {
    var 🐱 x
    let 🐱 y
    murr getX() kss 🐱 { mi x }
}
var Point p meow Point{10, 20}
🐾(p.getX())
''')
        structure, declaration, printing = program.statements
        self.assertEqual([f.mutable for f in structure.fields], [True, False])
        self.assertEqual(structure.methods[0].name, 'getX')
        self.assertIsInstance(declaration.value, ObjectCreationNode)
        self.assertEqual([a.value for a in declaration.value.arguments], [10, 20])
        self.assertIsInstance(printing.value, MemberCallNode)
        self.assertEqual(printing.value.object.name, 'p')

    def test_precedence_associativity_and_parentheses(self):
        value = parse('var 🐱 x meow -a + 2 * 3 - (8 - 4)').statements[0].value
        self.assertEqual(value.operator, '-')
        self.assertEqual(value.left.operator, '+')
        self.assertIsInstance(value.left.left, UnaryOpNode)
        self.assertEqual(value.left.right.operator, '*')
        self.assertEqual(value.right.operator, '-')
        repeated = parse('var 🐱 x meow --5').statements[0].value
        self.assertIsInstance(repeated.operand, UnaryOpNode)

    def test_nested_calls_read_and_field_assignment(self):
        program = parse('c.center.x meow add(add(1, 2), 📚()) c.center.move(10)')
        assignment, call = program.statements
        self.assertIsInstance(assignment, AssignmentNode)
        self.assertIsInstance(assignment.target, FieldAccessNode)
        self.assertEqual(assignment.target.object.field_name, 'center')
        self.assertIsInstance(assignment.value.arguments[0], CallNode)
        self.assertIsInstance(assignment.value.arguments[1], ReadNode)
        self.assertIsInstance(call.expression, MemberCallNode)

    def test_if_blocks_are_not_constructors(self):
        for condition in ['ready', 'p.ready', 'x meowmeow y', 'check()', 'true']:
            with self.subTest(condition=condition):
                node = parse(f'if {condition} {{ act() }} else {{ 🐾("no") }}').statements[0]
                self.assertEqual(len(node.then_body), 1)
                self.assertEqual(len(node.else_body), 1)
        node = parse('if ready { if other { act() } }').statements[0]
        self.assertIsInstance(node.condition, IdentifierNode)

    def test_constructors_in_conditions_and_arguments(self):
        for condition in ['Point{1, 2}.ready', '(Point{1, 2}).ready', 'check(Point{1, 2})']:
            with self.subTest(condition=condition):
                self.assertEqual(len(parse(f'if {condition} {{ act() }}').statements), 1)

    def test_syntax_errors_report_one_line(self):
        cases = [
            ('murr f() 🐱 { mi 1 }', 'expected KSS'),
            ('murr f() kss 🐱 {}', 'block must contain at least one statement'),
            ('mewi P { var 🐱 x murr f() kss 🐱 { mi 1 } var 🐱 y }',
             'fields must be declared before member functions'),
            ('mewi P {}', 'structure must contain at least one field'),
            ('foo(1,)', 'expected expression'),
            ('foo() meow 1', 'invalid assignment target'),
            ('🐾(📚(1))', 'expected RPAREN'),
            ('var 🐱 x meow 1 meowmeow 2 woem 3', 'unexpected token woem'),
            ('murr f() kss 🐱 { mi 1', 'expected }'),
        ]
        for source, message in cases:
            with self.subTest(source=source):
                error = io.StringIO()
                with contextlib.redirect_stderr(error), self.assertRaises(SystemExit) as raised:
                    parse(source)
                self.assertEqual(raised.exception.code, 1)
                self.assertEqual(len(error.getvalue().splitlines()), 1)
                self.assertRegex(error.getvalue(), r'^compilation error: line \d+:\d+: ')
                self.assertIn(message, error.getvalue())

    def test_semantic_checks_are_deferred(self):
        self.assertEqual(len(parse('mi missing() var Unknown p meow Unknown{}').statements), 2)


if __name__ == '__main__':
    unittest.main()
