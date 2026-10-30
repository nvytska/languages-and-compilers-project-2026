import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from compiler import CodeGenerator, Lexer, Parser, SemanticAnalyzer


ROOT = Path(__file__).resolve().parent.parent
LLC = shutil.which('llc')
if LLC is None:
    homebrew_llc = Path('/opt/homebrew/opt/llvm@22/bin/llc')
    if homebrew_llc.is_file():
        LLC = str(homebrew_llc)
CLANG = shutil.which('clang')
HAS_LLVM = importlib.util.find_spec('llvmlite') is not None
TRAP = 'var 🐱 overflowValue meow 2147483647 overflowValue meow overflowValue + 1'


@unittest.skipUnless(HAS_LLVM, 'llvmlite is required for LLVM tests')
class CodegenTests(unittest.TestCase):
    def module(self, source):
        program = Parser(Lexer(source.encode('utf-8')).tokenize()).parse_program()
        semantic = SemanticAnalyzer()
        semantic.analyze(program)
        return CodeGenerator(semantic).generate(program)

    def run_source(self, source, stdin="", via_cli=False):
        if not LLC or not CLANG:
            self.skipTest('llc and clang are required for executable tests')
        with tempfile.TemporaryDirectory(prefix='meow-codegen-') as directory:
            directory = Path(directory)
            module = directory / 'program.ll'
            obj = directory / 'program.o'
            executable = directory / 'program'
            if via_cli:
                source_path = directory / 'input.txt'
                source_path.write_text(source)
                subprocess.run([sys.executable, '-B', str(ROOT / 'compiler.py'),
                                str(source_path), str(module)],
                               check=True, capture_output=True, text=True)
            else:
                module.write_text(self.module(source))
            subprocess.run([LLC, '-filetype=obj', '-relocation-model=pic', str(module), '-o', str(obj)],
                           check=True, capture_output=True, text=True)
            subprocess.run([CLANG, '-fPIE', str(obj), '-o', str(executable)],
                           check=True, capture_output=True, text=True)
            return subprocess.run([str(executable)], input=stdin, capture_output=True, text=True, timeout=5)

    def assert_success(self, source):
        result = self.run_source(source)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))

    def test_requested_mixed_width_program(self):
        source = '''var 🐱 a meow 10
var 🐈 b meow 3000000000
var 🐈 c meow a + b
var 😺 different meow a woem b
if different { c meow c + 5 } else { c meow c - 5 }
'''
        module = self.module(source)
        self.assertIn('sext i32', module)
        self.assertIn('llvm.sadd.with.overflow.i64', module)
        self.assertIn('extractvalue', module)
        self.assertIn('unreachable', module)
        self.assert_success(source + f'if c woem 3000000015 {{ {TRAP} }}')

    def test_else_nested_if_and_local_shadowing(self):
        self.assert_success('''var 🐱 x meow 1
var 🐱 result meow 0
if false { result meow 99 } else {
    var 🐱 x meow 10
    if x meowmeow 10 { result meow x * 2 } else { result meow 99 }
}
''' + f'if x woem 1 {{ {TRAP} }} if result woem 20 {{ {TRAP} }}')

    def test_widening_initialization_assignment_and_signed_comparison(self):
        self.assert_success('''var 🐱 small meow -10
var 🐈 big meow small
if big woem small { ''' + TRAP + ''' }
big meow small + 1
if big woem -9 { ''' + TRAP + ''' }
if true meowmeow false { ''' + TRAP + ''' }
''')

    def test_checked_add_subtract_multiply_and_negation_overflow(self):
        cases = [
            ('🐱', '2000000000', 'a + a'),
            ('🐱', '-2147483648', 'a - 1'),
            ('🐱', '50000', 'a * a'),
            ('🐱', '-2147483648', '-a'),
            ('🐈', '9223372036854775807', 'a + 1'),
            ('🐈', '-9223372036854775808', 'a - 1'),
            ('🐈', '4000000000', 'a * a'),
            ('🐈', '-9223372036854775808', '-a'),
        ]
        for type_name, initial, expression in cases:
            with self.subTest(type_name=type_name, expression=expression):
                result = self.run_source(f'var {type_name} a meow {initial} '
                                         f'var {type_name} result meow {expression}')
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, 'runtime error: integer overflow\n')
                self.assertEqual(result.stderr, '')

    def test_minimum_literals_and_non_overflowing_arithmetic(self):
        self.assert_success('''var 🐱 a meow -2147483648
var 🐈 b meow -9223372036854775808
var 🐈 result meow b + 1
''' + f'if result woem -9223372036854775807 {{ {TRAP} }} '
        + f'if a woem -2147483648 {{ {TRAP} }}')
        self.assert_success('var 🐱 x meow -(2 + 3) * 4 + 20 '
                            f'if x woem 0 {{ {TRAP} }}')

    def test_widening_does_not_hide_i32_arithmetic_overflow(self):
        result = self.run_source('var 🐱 a meow 2000000000 var 🐈 result meow a + a')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, 'runtime error: integer overflow\n')

    def test_function_parameters_nested_calls_and_forward_declarations(self):
        self.assert_success('''murr twice(🐱 x) kss 🐱 { mi add(x, x) }
murr add(🐱 a, 🐱 b) kss 🐱 { mi a + b }
var 🐱 result meow add(twice(5), 7)
''' + f'if result woem 17 {{ {TRAP} }}')

    def test_function_argument_and_return_widening(self):
        source = '''murr big(🐈 value) kss 🐈 { mi value }
murr smallReturn() kss 🐈 { mi -10 }
var 🐈 result meow big(10) + smallReturn()
'''
        self.assertIn('sext i32', self.module(source))
        self.assert_success(source + f'if result woem 0 {{ {TRAP} }}')

    def test_recursion_and_mutual_recursion(self):
        self.assert_success('''murr down(🐱 n) kss 🐱 {
    if n meowmeow 0 { mi 0 } else { mi down(n - 1) }
}
murr even(🐱 n) kss 😺 {
    if n meowmeow 0 { mi true } else { mi odd(n - 1) }
}
murr odd(🐱 n) kss 😺 {
    if n meowmeow 0 { mi false } else { mi even(n - 1) }
}
var 🐱 result meow down(5)
var 😺 isEven meow even(6)
''' + f'if result woem 0 {{ {TRAP} }} if isEven woem true {{ {TRAP} }}')

    def test_returns_stop_code_generation_in_nested_blocks(self):
        self.assert_success('''murr choose(😺 flag) kss 🐱 {
    if flag {
        if true { mi 7 } else { mi 8 }
        var 🐱 dead meow 2147483647 + 1
    } else {
        mi 9
        var 🐱 dead meow 2147483647 + 1
    }
    var 🐱 dead meow 2147483647 + 1
}
murr fallback(😺 flag) kss 🐱 {
    if flag { mi 1 }
    mi 2
}
var 🐱 a meow choose(true)
var 🐱 b meow choose(false)
var 🐱 c meow fallback(false)
''' + f'if a woem 7 {{ {TRAP} }} if b woem 9 {{ {TRAP} }} if c woem 2 {{ {TRAP} }}')

    def test_user_function_names_do_not_clash_with_runtime(self):
        source = '''murr main() kss 🐱 { mi 1 }
murr printf() kss 🐱 { mi 2 }
murr puts() kss 🐱 { mi 3 }
murr exit() kss 🐱 { mi 4 }
var 🐱 result meow main() + printf() + puts() + exit()
'''
        module = self.module(source)
        for name in ['main', 'printf', 'puts', 'exit']:
            self.assertIn(f'@"mew_fn_{name}"', module)
        self.assert_success(source + f'if result woem 10 {{ {TRAP} }}')

    def test_function_globals_shadowing_and_standalone_calls(self):
        self.assert_success('''var 🐱 total meow 1
murr set(🐱 value) kss 🐱 { total meow value mi total }
murr local(🐱 total) kss 🐱 { mi total + 1 }
set(4)
var 🐱 result meow local(10)
''' + f'if total woem 4 {{ {TRAP} }} if result woem 11 {{ {TRAP} }}')

    def test_overflow_inside_function_terminates_program(self):
        result = self.run_source('''murr add(🐱 a, 🐱 b) kss 🐱 { mi a + b }
var 🐱 result meow add(2000000000, 2000000000)
''')
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (1, 'runtime error: integer overflow\n', ''))

    def test_member_setter_getter_and_implicit_forward_call(self):
        source = '''mewi Point {
    var 🐱 x
    murr twiceX() kss 🐱 { mi getX() + getX() }
    murr getX() kss 🐱 { mi x }
    murr setX(🐱 value) kss 🐱 { x meow value mi x }
}
var Point p meow Point{10}
p.setX(25)
var 🐱 result meow p.twiceX()
'''
        module = self.module(source)
        self.assertIn('@"mew_method_Point_setX"', module)
        self.assertIn('%"mew_struct_Point"* %"self"', module)
        self.assertIn('getelementptr inbounds', module)
        self.assert_success(source + f'if result woem 50 {{ {TRAP} }}')

    def test_nested_receivers_and_implicit_nested_fields(self):
        self.assert_success('''mewi Circle {
    var Point center
    murr getCenterX() kss 🐈 { mi center.x }
    murr update() kss 🐈 { mi center.setX(100) }
}
mewi Point {
    var 🐈 x
    murr setX(🐈 value) kss 🐈 { x meow value mi x }
}
var Circle c meow Circle{Point{10}}
c.center.setX(50)
c.update()
var 🐈 result meow c.getCenterX()
''' + f'if result woem 100 {{ {TRAP} }}')

    def test_member_lookup_shadowing_and_global_function_fallback(self):
        self.assert_success('''var 🐱 x meow 100
var 🐱 globalValue meow 7
murr helper(🐱 n) kss 🐱 { mi n + 1 }
murr getX() kss 🐱 { mi 999 }
mewi Point {
    var 🐱 x
    murr getX() kss 🐱 { mi x }
    murr parameter(🐱 x) kss 🐱 { mi x }
    murr local() kss 🐱 { let 🐱 x meow 9 mi x }
    murr internal() kss 🐱 { mi getX() }
    murr global() kss 🐱 { mi helper(globalValue) }
}
let Point p meow Point{3}
var 🐱 a meow p.parameter(5)
var 🐱 b meow p.local()
var 🐱 c meow p.internal()
var 🐱 d meow p.global()
''' + f'if a woem 5 {{ {TRAP} }} if b woem 9 {{ {TRAP} }} '
        + f'if c woem 3 {{ {TRAP} }} if d woem 8 {{ {TRAP} }} if x woem 100 {{ {TRAP} }}')

    def test_objects_are_values_and_temporaries_can_receive_readonly_calls(self):
        self.assert_success('''mewi Point { var 🐱 x murr get() kss 🐱 { mi x } }
murr make(🐱 x) kss Point { mi Point{x} }
murr copy(Point p) kss Point { mi p }
var Point p meow make(10)
var Point other meow copy(p)
other.x meow 20
var 🐱 a meow Point{30}.get()
var 🐱 b meow make(40).get()
var 🐱 c meow make(50).x
''' + f'if p.x woem 10 {{ {TRAP} }} if other.x woem 20 {{ {TRAP} }} '
        + f'if a woem 30 {{ {TRAP} }} if b woem 40 {{ {TRAP} }} if c woem 50 {{ {TRAP} }}')

    def test_struct_field_indices_local_storage_and_member_names(self):
        self.assert_success('''mewi A_B { var 🐱 x murr c() kss 🐱 { mi x } }
mewi A { var 😺 flag var 🐈 value murr B_c() kss 🐈 { mi value } }
murr work() kss 🐈 {
    var A a meow A{true, 3000000000}
    if true { var A a meow A{false, 12} a.value meow 15 }
    mi a.B_c()
}
var A_B first meow A_B{5}
var A second meow A{false, 9}
var 🐱 x meow first.c()
var 🐈 y meow second.B_c()
var 🐈 z meow work()
''' + f'if x woem 5 {{ {TRAP} }} if y woem 9 {{ {TRAP} }} if z woem 3000000000 {{ {TRAP} }}')

    def test_member_recursion_and_aggregate_results(self):
        self.assert_success('''mewi Counter {
    var 🐱 value
    murr run(🐱 n) kss 🐱 {
        if n meowmeow 0 { mi value } else { value meow value + 1 mi run(n - 1) }
    }
    murr copy() kss Counter { mi Counter{value} }
}
var Counter counter meow Counter{1}
var 🐱 result meow counter.run(4)
var Counter copied meow counter.copy()
''' + f'if result woem 5 {{ {TRAP} }} if copied.value woem 5 {{ {TRAP} }}')

    def test_member_overflow_still_terminates(self):
        result = self.run_source('''mewi P {
    var 🐱 x
    murr bump() kss 🐱 { x meow x + 1 mi x }
}
var P p meow P{2147483647}
p.bump()
''')
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (1, 'runtime error: integer overflow\n', ''))

    def test_io_end_to_end_fixtures(self):
        paths = sorted((ROOT / 'tests' / 'ok').glob('*.txt'))
        self.assertGreaterEqual(len(paths), 20)
        for path in paths:
            with self.subTest(program=path.name):
                input_path = path.with_suffix('.in')
                stdin = input_path.read_text() if input_path.exists() else ''
                result = self.run_source(path.read_text(), stdin=stdin, via_cli=True)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, path.with_suffix('.expected').read_text())
                self.assertEqual(result.stderr, '')

    def test_io_runtime_declarations_and_string_cache(self):
        program = Parser(Lexer('var 🐱 x meow 📚() 🐾("repeat") 🐾("repeat")'.encode()).tokenize()).parse_program()
        semantic = SemanticAnalyzer()
        semantic.analyze(program)
        generator = CodeGenerator(semantic)
        module = generator.generate(program)
        self.assertIn('declare i32 @"printf"(i8*', module)
        self.assertIn('declare i32 @"scanf"(i8*', module)
        self.assertEqual(module.count('c"repeat\\00"'), 1)
        self.assertIs(generator.fmt_read_i32, generator.fmt_i32)

    def test_command_line_compile_and_error_contract(self):
        with tempfile.TemporaryDirectory(prefix='meow-cli-') as directory:
            directory = Path(directory)
            source = directory / 'input.txt'
            output = directory / 'output.ll'
            source.write_text('var 🐈 x meow 3000000000')
            command = [sys.executable, '-B', str(ROOT / 'compiler.py'), str(source), str(output)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))
            self.assertIn('store i64 3000000000', output.read_text())
            output.unlink()
            for invalid in [
                'var 🐈 x meow 99999999999999999999',
                'var 🐱 x meow true', 'var 🐱 x meow', 'var 🐱 x meow @',
                'mi 1',
                'murr f(🐱 x) kss 🐱 { mi x } f()',
                'murr f(🐱 x) kss 🐱 { mi x } f(1, 2)',
                'murr f(🐱 x) kss 🐱 { mi x } f(true)',
                'murr f() kss 🐱 { mi true }',
                'mewi P { var 🐱 x murr set() kss 🐱 { x meow 2 mi x } } '
                'let P p meow P{1} p.set()',
                'mewi P { var P recursive }',
            ]:
                with self.subTest(source=invalid):
                    source.write_text(invalid)
                    result = subprocess.run(command, capture_output=True, text=True)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(result.stdout, '')
                    self.assertEqual(len(result.stderr.splitlines()), 1)
                    self.assertTrue(result.stderr.startswith('compilation error: line '))
                    self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
