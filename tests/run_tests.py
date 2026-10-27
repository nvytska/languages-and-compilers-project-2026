"""Run compiler fixtures, comparing output bytes and preserving Stage 1 tests."""

import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
COMPILER = ROOT / 'compiler.py'
TESTS = ROOT / 'tests'


def find_tool(name):
    configured = os.environ.get(name.upper())
    if configured:
        return shutil.which(configured)
    found = shutil.which(name)
    if found:
        return found
    for prefix in (Path('/opt/homebrew/opt'), Path('/usr/local/opt')):
        for llvm in sorted(prefix.glob('llvm*'), reverse=True):
            candidate = llvm / 'bin' / name
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate)
    return None


class TestRunner:
    def __init__(self, llc, clang):
        self.llc = llc
        self.clang = clang
        self.passed = 0
        self.failed = 0

    def execute(self, command, stdin=b''):
        return subprocess.run(command, input=stdin, capture_output=True, timeout=20, cwd=ROOT)

    def require(self, condition, message):
        if not condition:
            raise AssertionError(message)

    def check_compiler_success(self, result, output):
        self.require(result.returncode == 0, f'compiler exited {result.returncode}: {result.stderr!r}')
        self.require(result.stdout == b'' and result.stderr == b'',
                     f'unexpected compiler output: {result.stdout!r} {result.stderr!r}')
        self.require(output.is_file(), 'compiler did not create .ll')

    def check_compiler_error(self, result, expected):
        self.require(result.returncode != 0, 'compiler accepted invalid program')
        self.require(result.stdout == b'', f'unexpected stdout: {result.stdout!r}')
        self.require(len(result.stderr.splitlines()) == 1
                     and result.stderr.startswith(b'compilation error: line '),
                     f'expected one compilation error line, got {result.stderr!r}')
        self.require(result.stderr == expected,
                     f'error differs\n  expected: {expected!r}\n  actual:   {result.stderr!r}')

    def run_ast(self, source, invalid):
        expected = source.with_suffix('.expected').read_bytes()
        result = self.execute([sys.executable, '-B', str(COMPILER), '--ast', str(source)])
        if invalid:
            self.check_compiler_error(result, expected)
        else:
            self.require(result.returncode == 0 and result.stderr == b'',
                         f'AST compiler failed: {result.stderr!r}')
            self.require(result.stdout == expected,
                         f'AST differs\n  expected: {expected!r}\n  actual:   {result.stdout!r}')

    def run_compile(self, source, invalid=False, end_to_end=False):
        with tempfile.TemporaryDirectory(prefix='meow-tests-') as temp:
            temp = Path(temp)
            output = temp / 'output.ll'
            result = self.execute([sys.executable, '-B', str(COMPILER), str(source), str(output)])
            if invalid:
                self.check_compiler_error(result, source.with_suffix('.expected').read_bytes())
                self.require(not output.exists(), 'compiler created .ll after an error')
                return
            self.check_compiler_success(result, output)
            obj = temp / 'output.o'
            result = self.execute([self.llc, '-filetype=obj', '-relocation-model=pic',
                                   str(output), '-o', str(obj)])
            self.require(result.returncode == 0, f'llc failed: {result.stderr!r}')
            if not end_to_end:
                return
            executable = temp / 'program'
            result = self.execute([self.clang, '-fPIE', str(obj), '-o', str(executable)])
            self.require(result.returncode == 0, f'clang failed: {result.stderr!r}')
            input_file = source.with_suffix('.in')
            stdin = input_file.read_bytes() if input_file.exists() else b''
            result = self.execute([str(executable)], stdin)
            expected = source.with_suffix('.expected').read_bytes()
            self.require(result.returncode == 0, f'program exited {result.returncode}: '
                         f'stdout={result.stdout!r}, stderr={result.stderr!r}')
            self.require(result.stderr == b'', f'unexpected runtime stderr: {result.stderr!r}')
            self.require(result.stdout == expected,
                         f'stdout differs\n  expected: {expected!r}\n  actual:   {result.stdout!r}')

    def run_group(self, directory, operation):
        paths = sorted(directory.glob('*.txt'))
        if not paths:
            self.failed += 1
            print(f'FAIL {directory.relative_to(ROOT)}: no tests found')
        for source in paths:
            name = source.relative_to(ROOT)
            try:
                operation(source)
            except (AssertionError, OSError, subprocess.TimeoutExpired) as error:
                self.failed += 1
                print(f'FAIL {name}\n  {error}')
            else:
                self.passed += 1
                print(f'PASS {name}')


def main():
    llc, clang = find_tool('llc'), find_tool('clang')
    if importlib.util.find_spec('llvmlite') is None:
        print('FAIL setup: install requirements.txt using the Python running this script')
        return 1
    if not llc or not clang:
        print('FAIL setup: llc and clang are required; add them to PATH or set LLC/CLANG')
        return 1
    runner = TestRunner(llc, clang)
    ok = list((TESTS / 'ok').glob('*.txt'))
    errors = list((TESTS / 'err').glob('*.txt'))
    if len(ok) < 20 or len(errors) < 20 or not any(p.with_suffix('.in').exists() for p in ok):
        runner.failed += 1
        print('FAIL coverage: require 20 E2E valid, 20 invalid, and an E2E .in file')
    groups = [
        (TESTS / 'valid', lambda p: runner.run_ast(p, False)),
        (TESTS / 'invalid', lambda p: runner.run_ast(p, True)),
        (TESTS / 'semantic' / 'valid', lambda p: runner.run_compile(p)),
        (TESTS / 'semantic' / 'invalid', lambda p: runner.run_compile(p, invalid=True)),
        (TESTS / 'ok', lambda p: runner.run_compile(p, end_to_end=True)),
        (TESTS / 'err', lambda p: runner.run_compile(p, invalid=True)),
    ]
    for directory, operation in groups:
        print(f'\n=== {directory.relative_to(ROOT)} ===')
        runner.run_group(directory, operation)
    print(f'\nPassed: {runner.passed}\nFailed: {runner.failed}')
    return 1 if runner.failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
