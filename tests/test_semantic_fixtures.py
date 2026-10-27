import contextlib
import io
from pathlib import Path
import unittest

from compiler import Lexer, Parser, SemanticAnalyzer


FIXTURES = Path(__file__).parent / 'semantic'


class SemanticFixtureTests(unittest.TestCase):
    def analyze_file(self, path):
        program = Parser(Lexer(path.read_bytes()).tokenize()).parse_program()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(program)
        return analyzer

    def test_valid_programs(self):
        paths = sorted((FIXTURES / 'valid').glob('*.txt'))
        self.assertEqual(len(paths), 6)
        for path in paths:
            with self.subTest(program=path.name):
                analyzer = self.analyze_file(path)
                self.assertEqual(analyzer.scopes, [])

    def test_invalid_programs(self):
        paths = sorted((FIXTURES / 'invalid').glob('*.txt'))
        self.assertEqual(len(paths), 10)
        for path in paths:
            with self.subTest(program=path.name):
                error = io.StringIO()
                with contextlib.redirect_stderr(error), self.assertRaises(SystemExit) as raised:
                    self.analyze_file(path)
                self.assertEqual(raised.exception.code, 1)
                self.assertEqual(error.getvalue(), path.with_suffix('.expected').read_text())


if __name__ == '__main__':
    unittest.main()
