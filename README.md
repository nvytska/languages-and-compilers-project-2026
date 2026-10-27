# MeowLang

MeowLang is a small custom programming language developed for Stages 1 and 2 of the Languages and Compilers Design course project.

The language uses cat-themed keywords and emoji syntax while keeping the grammar and semantics intentionally simple. The compiler includes a hand-written lexer, recursive-descent parser, semantic analysis, and LLVM IR code generation through `llvmlite.ir`.

## Features

MeowLang supports:

- mutable and immutable variables;
- 32-bit and 64-bit signed integers;
- booleans;
- arithmetic with `+`, `-`, and `*`;
- equality and inequality comparisons;
- integer widening from `i32` to `i64`;
- compile-time integer literal overflow checks;
- runtime arithmetic overflow checks;
- assignment;
- `if` and optional `else`;
- nested blocks and scopes;
- functions with typed parameters and result types;
- nested function calls;
- recursive functions;
- calls to functions declared later in the program;
- structures with mutable and immutable fields;
- object creation;
- chained field access;
- member functions;
- input using `📚()`;
- output using `🐾(...)`;
- LLVM IR generation.

The lexer is implemented manually as a state machine over UTF-8 bytes.

The parser is implemented manually using recursive descent.

Semantic analysis runs as a separate pass before LLVM code generation.

---

## Types

MeowLang has three built-in types.

| Syntax | Type |
| --- | --- |
| `🐱` | `i32` |
| `🐈` | `i64` |
| `😺` | `bool` |

Structure names are also valid types.

Example:

```text
var 🐱 age meow 19
let 🐈 population meow 8000000000
var 😺 sleepy meow true
```

A structure can be used as a type:

```text
mewi Point {
    var 🐱 x
    var 🐱 y
}

var Point p meow Point{10, 20}
```

---

## Variables

### Mutable variables

Mutable variables are declared using `var`.

```text
var 🐱 count meow 5
```

A mutable variable may later be assigned another compatible value:

```text
count meow 10
```

### Immutable variables

Immutable variables are declared using `let`.

```text
let 🐈 limit meow 9000000000
```

An immutable variable cannot be assigned another value after initialization.

---

## Assignment

The keyword `meow` is used as the assignment operator.

```text
var 🐱 x meow 5
x meow 10
```

The left side may also be a field chain:

```text
p.x meow 20
circle.center.x meow 30
```

An assignment through a field chain is allowed only when the variable and every field that must be modified through the chain are mutable.

---

## Integer Literals and Numeric Types

Integer literals use the narrowest signed integer type that can hold their value.

Examples:

```text
10
```

has type `i32`.

```text
3000000000
```

has type `i64`.

The supported signed ranges are:

```text
i32: -2147483648 to 2147483647
i64: -9223372036854775808 to 9223372036854775807
```

A literal outside the `i64` range is a compilation error.

Example:

```text
var 🐈 x meow 9223372036854775808
```

is invalid.

Negative integer expressions are supported:

```text
var 🐱 temperature meow -12
```

---

## Integer Widening

MeowLang supports one implicit numeric conversion:

```text
i32 -> i64
```

For example:

```text
var 🐱 small meow 10
var 🐈 large meow small
```

is valid.

Narrowing is not allowed:

```text
var 🐈 large meow 3000000000
var 🐱 small meow large
```

is invalid because an `i64` value cannot implicitly become an `i32`.

The same widening rule applies to:

- variable initialization;
- assignment;
- function arguments;
- member function arguments;
- return values;
- structure field initialization.

---

## Arithmetic

MeowLang supports:

```text
+
-
*
```

Multiplication has higher precedence than addition and subtraction.

Example:

```text
var 🐱 result meow 10 + 5 * 2
```

produces `20`.

Arithmetic is only valid for integer values.

The result has the wider type of its operands:

```text
i32 + i32 -> i32
i32 + i64 -> i64
i64 + i32 -> i64
i64 + i64 -> i64
```

For example:

```text
var 🐱 a meow 10
var 🐈 b meow 3000000000
var 🐈 c meow a + b
```

is valid.

---

## Overflow

MeowLang checks two kinds of integer overflow.

### Literal overflow

A literal that does not fit into `i64` is rejected during semantic analysis.

```text
var 🐈 x meow 999999999999999999999
```

produces a compilation error.

### Arithmetic overflow

Overflow caused by runtime arithmetic is checked in the generated LLVM code.

For example:

```text
var 🐱 a meow 2000000000
var 🐱 b meow 2000000000
var 🐱 c meow a + b
```

is valid at compile time because both operands are valid `i32` values.

The addition itself overflows at runtime.

Arithmetic overflow terminates the program and reports:

```text
runtime error: integer overflow
```

Checked arithmetic is generated for `+`, `-`, and `*`, including nonliteral unary negation. The runtime error is printed to stdout with a final newline, and the executable exits with code `1`.

---

## Comparison Operators

MeowLang uses custom equality operators.

| Syntax | Meaning |
| --- | --- |
| `meowmeow` | equality (`==`) |
| `woem` | inequality (`!=`) |

Examples:

```text
x meowmeow 5
x woem 10
```

Two integer values may be compared even when they have different widths. The `i32` operand is widened to `i64` before the comparison when necessary.

```text
var 🐱 a meow 10
var 🐈 b meow 3000000000
var 😺 different meow a woem b
```

Booleans may only be compared with booleans.

The result of every comparison is `bool`.

---

## Boolean Values

Boolean literals are:

```text
true
false
```

Example:

```text
var 😺 ready meow true
```

Booleans cannot participate in integer arithmetic.

---

## If / Else

An `if` condition must have type `bool`.

```text
var 😺 ready meow true

if ready {
    🐾("ready")
}
```

An `else` clause is optional:

```text
if ready {
    🐾("ready")
} else {
    🐾("not ready")
}
```

Every `if` and `else` block must contain at least one statement.

Blocks may be nested.

```text
if ready {
    if count woem 0 {
        count meow count + 1
    }
}
```

Each block introduces a scope.

---

## Functions

Functions are declared using `murr`.

The result type follows `kss`.

A value is returned using `mi`. Parameters are immutable and must have unique names. An ordinary function can see its parameters, visible locals, and global variables declared before the function declaration; locals and parameters take precedence over globals. `mi` outside a function or member function is rejected.

Example:

```text
murr add(🐱 a, 🐱 b) kss 🐱 {
    mi a + b
}
```

Function calls are expressions:

```text
var 🐱 result meow add(10, 20)
```

They may also be nested:

```text
var 🐱 result meow add(add(1, 2), 3)
```

### Function argument rules

The number of arguments must exactly match the number of parameters.

Each argument must be assignable to the corresponding parameter type.

The normal widening rule applies, so an `i32` argument may be passed to an `i64` parameter.

Example:

```text
murr identity(🐈 value) kss 🐈 {
    mi value
}

var 🐈 result meow identity(10)
```

### Function result rules

The value used with `mi` must be assignable to the declared result type.

```text
murr big() kss 🐈 {
    mi 10
}
```

is valid because `i32` may widen to `i64`.

A function must return a value on every possible control-flow path.

### Recursion

Functions may call themselves.

```text
murr down(🐱 n) kss 🐱 {
    if n meowmeow 0 {
        mi 0
    } else {
        mi down(n - 1)
    }
}
```

### Forward calls

A function may call a function declared later in the file.

```text
murr first() kss 🐱 {
    mi second()
}

murr second() kss 🐱 {
    mi 42
}
```

All function signatures are collected before function bodies are checked and generated.

---

## Structures

Structures are declared using `mewi`. Each structure must have at least one field, and all fields must precede member functions. Recursive by-value field layouts are rejected because they have no finite size.

```text
mewi Point {
    var 🐱 x
    var 🐱 y
}
```

Fields may be mutable using `var` or immutable using `let`.

```text
mewi User {
    let 🐱 id
    var 😺 active
}
```

### Object creation

An object is created using the structure name followed by values in braces.

```text
var Point p meow Point{10, 20}
```

Constructor values are positional and correspond to fields in declaration order.

Every field must receive exactly one value.

The value must be assignable to the field type.

Example:

```text
mewi Data {
    var 🐈 value
}

var Data d meow Data{10}
```

is valid because `10` is `i32` and may widen to `i64`.

---

## Field Access

Fields are accessed with `.`.

```text
var 🐱 value meow p.x
```

Field accesses may be chained:

```text
circle.center.x
```

Example:

```text
mewi Point {
    var 🐱 x
    var 🐱 y
}

mewi Circle {
    var Point center
    var 🐱 radius
}

var Circle c meow Circle{Point{10, 20}, 5}

🐾(c.center.x)
```

Accessing a field that does not exist is a compilation error.

---

## Field Mutability

Assignment is allowed only through a mutable chain.

Example:

```text
mewi Point {
    var 🐱 x
}

var Point p meow Point{10}
p.x meow 20
```

is valid.

If an intermediate field is immutable, assignment through it is invalid:

```text
mewi Point {
    var 🐱 x
}

mewi Circle {
    let Point center
}

var Circle c meow Circle{Point{10}}

c.center.x meow 20
```

is rejected because `center` is immutable.

---

## Member Functions

Member functions are declared inside a structure using the same `murr` syntax as normal functions.

```text
mewi Point {
    var 🐱 x

    murr getX() kss 🐱 {
        mi x
    }
}
```

They are called on an object:

```text
var Point p meow Point{10}
var 🐱 value meow p.getX()
```

Inside a member function:

- structure fields are visible directly by name;
- other member functions are visible directly by name;
- global variables remain visible when they are not shadowed.

Example:

```text
mewi Point {
    var 🐱 x

    murr getX() kss 🐱 {
        mi x
    }

    murr twiceX() kss 🐱 {
        mi getX() + getX()
    }
}
```

---

## Name Lookup Inside Member Functions

When a name is used inside a member function, MeowLang resolves it in this order:

1. parameters and local variables;
2. fields of the current structure;
3. global variables.

The first matching declaration is used.

For example:

```text
var 🐱 x meow 100

mewi Point {
    var 🐱 x

    murr example(🐱 x) kss 🐱 {
        mi x
    }
}
```

Inside `example`, `x` refers to the parameter because parameters and locals have higher priority than fields and globals.

---

## Mutating Member Functions

A member function is considered mutating when it assigns to a field of its object, directly or through other member functions. This includes changes to nested fields; mutation flags propagate until stable.

Example:

```text
mewi Point {
    var 🐱 x

    murr setX(🐱 value) kss 🐱 {
        x meow value
        mi x
    }
}
```

A mutating member function may only be called through a receiver chain that is mutable at every step. A non-mutating member function may be called on a constant or temporary object.

Valid:

```text
var Point p meow Point{10}
p.setX(20)
```

Invalid:

```text
let Point p meow Point{10}
p.setX(20)
```

---

## Input

Input uses the `📚()` built-in expression.

```text
var 🐱 value meow 📚()
```

`📚()` reads one integer from standard input and produces an `i32` value.

At LLVM level, input is implemented using the C library function `scanf`.

---

## Output

Output uses the `🐾(...)` built-in.

It supports:

- `i32`;
- `i64`;
- `bool`;
- string literals;
- structures.

Examples:

```text
🐾(42)
🐾(3000000000)
🐾(true)
🐾("hello")
```

Output:

```text
42
3000000000
true
hello
```

`i32` values are printed using `%d`.

`i64` values are printed using `%lld`.

Boolean values are printed as:

```text
true
false
```

rather than as `1` and `0`.

Every `🐾(...)` statement prints a newline after the complete value.

String literals are supported as direct values of `🐾(...)`; MeowLang does not define a general string variable type.

---

## Printing Structures

Structures are printed using the structure name followed by their field names and values.

Example:

```text
mewi Point {
    var 🐱 x
    var 🐱 y
}

var Point p meow Point{10, 20}

🐾(p)
```

Output:

```text
Point{x: 10, y: 20}
```

Nested structures are printed recursively.

Example:

```text
mewi Point {
    var 🐱 x
    var 🐱 y
}

mewi Circle {
    var Point center
    var 🐱 radius
}

var Circle c meow Circle{Point{10, 20}, 5}

🐾(c)
```

Output:

```text
Circle{center: Point{x: 10, y: 20}, radius: 5}
```

The compiler does not contain special printing code for individual structure names. It walks the structure's field metadata, so newly declared structures can be printed without modifying the compiler.

---

## Example Stage 2 Program

```text
mewi Point {
    var 🐱 x
    var 🐱 y

    murr sum() kss 🐱 {
        mi x + y
    }

    murr setX(🐱 value) kss 🐱 {
        x meow value
        mi x
    }
}

murr add(🐱 a, 🐱 b) kss 🐱 {
    mi a + b
}

var 🐱 input meow 📚()

var Point p meow Point{
    input,
    add(10, 20)
}

🐾(p)
🐾(p.sum())

p.setX(50)

🐾(p)
```

For input:

```text
5
```

the program prints:

```text
Point{x: 5, y: 30}
35
Point{x: 50, y: 30}
```

---

## Grammar

The complete EBNF grammar is stored in:

```text
grammar.ebnf
```

The grammar contains the syntax and lexical rules for:

- variables;
- assignments;
- arithmetic;
- comparisons;
- control flow;
- functions;
- structures;
- member functions;
- function and member calls;
- object creation;
- field access;
- input;
- output;
- literals.

The parser accepts constructs described by `grammar.ebnf`.

---

## Lexer

The lexer is implemented manually as a state machine over UTF-8 bytes.

It does not use regular expressions, a lexer generator, or `split()` as a replacement for lexical analysis.

The lexer recognizes:

- keywords;
- identifiers;
- integer literals;
- string literals used by print;
- punctuation;
- arithmetic operators;
- custom operators;
- emoji type names;
- emoji input/output built-ins.

Each token stores:

- token kind;
- original text;
- line;
- column.

Whitespace consists of spaces, tabs, carriage returns, and newlines and otherwise separates tokens.

Lexical errors use the standard error format:

```text
compilation error: line L:C: message
```

---

## Parser

The parser is implemented manually using recursive descent.

It consumes the token stream using `peek` and `eat` operations and creates an Abstract Syntax Tree.

The AST contains nodes for the Stage 1 and Stage 2 constructs, including:

```text
ProgramNode

Statements:
- VarDeclNode
- AssignmentNode
- IfNode
- FunctionDeclNode
- StructDeclNode
- ReturnNode
- PrintNode
- ExprStmtNode

Expressions:
- IntegerLiteralNode
- BooleanLiteralNode
- StringLiteralNode
- IdentifierNode
- BinaryOpNode
- UnaryOpNode
- ComparisonNode
- CallNode
- MemberCallNode
- FieldAccessNode
- ObjectCreationNode
- ReadNode
```

AST nodes keep their source positions.

The AST dump includes the information needed for Stage 2 constructs, such as parameter and result types, field mutability, call arguments, and member access structure.

---

## Semantic Analysis

Semantic analysis is a separate pass that runs after parsing and before LLVM code generation.

No semantic rule relies on LLVM or `llvmlite` to detect invalid source programs.

The semantic analyzer maintains information about:

- variables and their types and mutability;
- function parameter and result types;
- structures;
- ordered structure fields;
- field types and mutability;
- field indices;
- member function signatures;
- whether a member function mutates its object.

It checks:

- declaration before use;
- duplicate declarations in the same scope;
- assignment mutability;
- variable initialization types;
- assignment types;
- integer widening rules;
- integer literal overflow;
- arithmetic operand types;
- comparison operand types;
- boolean `if` conditions;
- function argument count;
- function argument types;
- function return types;
- return on all required control-flow paths;
- structure constructor argument count;
- structure constructor argument types;
- field existence;
- member function existence;
- member function argument count and types;
- field-chain mutability;
- mutating member calls on immutable objects.

If semantic analysis fails, LLVM generation is not started.

---

## LLVM IR Generation

LLVM IR is generated using the `llvmlite.ir` builder API.

The compiler does not construct LLVM IR by manually concatenating IR strings.

### Variables

Variables are represented by LLVM storage locations and are loaded or stored when used.

### Integer widening

When semantic analysis allows:

```text
i32 -> i64
```

LLVM code generation emits a signed extension (`sext`).

### Arithmetic

Arithmetic uses the correct LLVM integer width.

Checked signed arithmetic is used for overflow-sensitive operations.

### Control flow

`if` and `else` are represented using LLVM basic blocks and conditional branches.

### Functions

All function declarations are added to the LLVM module before any function body is generated.

This enables recursion and calls to functions declared later in the source file.

User function names receive a compiler prefix in LLVM to avoid clashes with runtime functions such as `main`, `printf`, and `scanf`.

### Structures

Each MeowLang structure becomes an LLVM identified structure type.

Objects are stored in allocated structure memory.

Fields are accessed using LLVM `getelementptr` with the field index stored in the semantic symbol table.

### Member functions

Each member function becomes a separate LLVM function.

Its first hidden parameter is a pointer to the object on which the member function was called.

### Input and output

The compiler declares `scanf` and `printf` in the LLVM module.

Their implementations are provided by the C library when the generated object file is linked using `clang`.

---

## Running the Compiler

### Requirements

The project requires:

- Python 3.10 or newer;
- `llvmlite`;
- LLVM tools, including `llc`;
- `clang`.

Example environment setup:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

LLVM and Clang must also be installed on the system.

---

## Print the AST

Run:

```bash
python3 compiler.py --ast input.txt
```

This prints the AST and does not generate LLVM output.

---

## Generate LLVM IR

Run:

```bash
python3 compiler.py input.txt output.ll
```

If compilation succeeds, `output.ll` contains the LLVM module generated through `llvmlite.ir`.

---

## Build and Run a Compiled Program

Compile LLVM IR into an object file:

```bash
llc -filetype=obj -relocation-model=pic output.ll -o output.o
```

Link it:

```bash
clang -fPIE output.o -o program
```

Run it:

```bash
./program
```

For programs that read standard input:

```bash
./program < input.in
```

---

## Errors

Lexical, syntax, and semantic errors use the same format:

```text
compilation error: line L:C: message
```

On a compilation error:

- exactly one error line is written to `stderr`;
- the compiler exits with a non-zero status;
- no LLVM output file is produced;
- no Python traceback is printed.

Example:

```text
compilation error: line 3:5: structure 'Point' has no field 'z'
```

Runtime arithmetic overflow is not a compilation error because it depends on runtime values.

---

## Tests

The project includes Stage 1 and Stage 2 tests covering both valid and invalid programs.

The test suite contains more than the required:

- 20 valid programs;
- 20 invalid programs;
- 10 end-to-end compilation and execution tests;
- at least one test using standard input from a `.in` file.

Valid end-to-end tests:

1. compile a MeowLang source file to LLVM IR;
2. build the LLVM IR;
3. run the resulting program;
4. compare `stdout` exactly with the expected output.

Invalid tests compare the exact expected error message and also verify that no LLVM output file is created.

Input tests use:

```text
NAME.in
```

as the program's standard input.

The expected file contains only what the program itself prints.

Run the test suite with:

```bash
python3 tests/run_tests.py
```

The current test suite completes successfully with:

```text
Passed: 108
Failed: 0
```

---

## Project Files

The Stage 2 submission must contain the compiler source, grammar, documentation, AI disclosure, and tests. The layout below lists the required submission contents; `ai_usage_2.txt` still needs to be added.

Example layout:

```text
compiler.py
requirements.txt
grammar.ebnf
README.md
run_tests.sh
ai_usage_2.txt

tests/
├── ok/
├── err/
└── run_tests.py
```

Generated files such as LLVM `.ll` files, object files, executables, and temporary scratch files are not part of the submission.

---

## AI Usage

AI usage for Stage 2 must be documented separately in:

```text
ai_usage_2.txt
```

`ai_usage_2.txt` has not yet been added. It must be completed before submission, including the author's own explanation of their understanding.

The disclosure must describe:

- the AI tools used;
- prompts or transcript links;
- which suggestions or code were used;
- what was changed and why;
- the author's understanding of AI-assisted parts of the implementation.

---

## Summary

MeowLang Stage 2 implements the complete pipeline:

```text
source code
    ↓
lexer
    ↓
tokens
    ↓
recursive-descent parser
    ↓
AST
    ↓
semantic analysis
    ↓
checked AST / symbol information
    ↓
LLVM IR generation
    ↓
llc
    ↓
object file
    ↓
clang + C runtime
    ↓
executable program
```

The language now supports typed variables, arithmetic, comparisons, control flow, functions, recursion, structures, fields, member functions, input/output, semantic checking, integer overflow protection, and LLVM code generation.
