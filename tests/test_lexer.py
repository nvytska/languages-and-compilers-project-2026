import contextlib
import io
import unittest

from compiler import Lexer, TokenKind


class LexerTests(unittest.TestCase):
    def tokens(self, source):
        return Lexer(source.encode("utf-8")).tokenize()

    def test_keywords_and_identifier_boundaries(self):
        tokens = self.tokens("murr mewi kss mi murrx mewi_1 _mi")
        self.assertEqual([t.kind for t in tokens], [
            TokenKind.MURR, TokenKind.MEWI, TokenKind.KSS, TokenKind.MI,
            TokenKind.IDENTIFIER, TokenKind.IDENTIFIER,
            TokenKind.IDENTIFIER, TokenKind.EOF,
        ])

    def test_minus_is_separate_with_or_without_spaces(self):
        tokens = self.tokens("-5 a-5 a - 5 + 2*3")
        self.assertEqual([t.text for t in tokens], [
            "-", "5", "a", "-", "5", "a", "-", "5",
            "+", "2", "*", "3", "",
        ])
        self.assertEqual(tokens[0].kind, TokenKind.MINUS)
        self.assertEqual(tokens[1].kind, TokenKind.INTEGER)

    def test_calls_chains_and_emoji_positions(self):
        tokens = self.tokens("🐾(p.center.x, 📚())\nvar 🐱 n meow 1")
        self.assertEqual(
            [(t.kind.name, t.line, t.column) for t in tokens[:13]],
            [("PRINT", 1, 1), ("LPAREN", 1, 2), ("IDENTIFIER", 1, 3),
             ("DOT", 1, 4), ("IDENTIFIER", 1, 5), ("DOT", 1, 11),
             ("IDENTIFIER", 1, 12), ("COMMA", 1, 13), ("READ", 1, 15),
             ("LPAREN", 1, 16), ("RPAREN", 1, 17), ("RPAREN", 1, 18),
             ("VAR", 2, 1)],
        )

    def test_strings_are_unicode_without_escape_processing(self):
        tokens = self.tokens('"Привіт 🐱" "" "a\\b"')
        self.assertEqual([t.text for t in tokens], ["Привіт 🐱", "", "a\\b", ""])
        self.assertEqual(tokens[1].column, 12)
        self.assertTrue(all(t.kind == TokenKind.STRING for t in tokens[:-1]))

    def test_unterminated_strings_report_opening_quote(self):
        for source in ['  "hello', '  "hello\nnext', '  "hello\r\nnext']:
            with self.subTest(source=source):
                error = io.StringIO()
                with contextlib.redirect_stderr(error), self.assertRaises(SystemExit) as raised:
                    self.tokens(source)
                self.assertEqual(raised.exception.code, 1)
                self.assertEqual(error.getvalue(),
                                 "compilation error: line 1:3: unterminated string literal\n")

    def test_invalid_utf8_in_string_is_a_compilation_error(self):
        error = io.StringIO()
        with contextlib.redirect_stderr(error), self.assertRaises(SystemExit):
            Lexer(b'"\xff"').tokenize()
        self.assertEqual(error.getvalue(),
                         "compilation error: line 1:1: invalid UTF-8 in string literal\n")

    def test_stage2_example(self):
        source = '''mewi Point {
    var 🐱 x
    var 🐱 y
    murr getX() kss 🐱 {
        mi x
    }
}
murr add(🐱 a, 🐱 b) kss 🐱 {
    mi a + b
}
var Point p meow Point{10, 20}
var 🐱 n meow 📚()
🐾("hello")
🐾(p)
'''
        tokens = self.tokens(source)
        self.assertEqual(tokens[-1].kind, TokenKind.EOF)
        self.assertEqual(tokens[-1].line, 15)
        self.assertEqual(sum(t.kind == TokenKind.MURR for t in tokens), 2)
        self.assertEqual(sum(t.kind == TokenKind.PRINT for t in tokens), 2)
        self.assertEqual(sum(t.kind == TokenKind.READ for t in tokens), 1)


if __name__ == "__main__":
    unittest.main()
