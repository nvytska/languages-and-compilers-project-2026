# MeowLang

MeowLang is a small custom programming language created for Stage 1 of the Languages and Compilers Design course project.

The language uses cat-themed syntax while keeping the grammar intentionally simple.

## Features

MeowLang supports:

- mutable variables
- immutable variables
- 32-bit integers
- 64-bit integers
- booleans
- assignment
- equality and inequality comparisons
- negative integer literals
- `if`
- optional `else`
- nested `if` statements

The lexer is implemented manually as a state machine over UTF-8 bytes.

The parser is implemented manually using recursive descent.

## Types

MeowLang uses cat emojis as type names.

| Syntax | Type   |
| ------ | ------ |
| `🐱`   | `i32`  |
| `🐈`   | `i64`  |
| `😺`   | `bool` |

Example:

```javascript
var 🐱 age meow 19
let 🐈 population meow 8000000000
var 😺 sleepy meow true
```

## Variables

### Mutable variables

Use `var`:

```javascript
var 🐱 count meow 5
```

### Immutable variables

Use `let`:

```javascript
let 🐈 limit meow 9000000000
```

## Assignment

The keyword `meow` is used instead of `=`.

```javascript
var 🐱 x meow 5
x meow 10
```

## Comparison Operators

MeowLang uses custom comparison operators.

| Syntax     | Meaning           |
| ---------- | ----------------- |
| `meowmeow` | equality (`==`)   |
| `woem`     | inequality (`!=`) |

Examples:

```css
x meowmeow 5
x woem 10
```

## Boolean Values

Boolean literals use:

```
true
false
```

Example:

```javascript
var 😺 ready meow true
```

## Negative Integers

Negative integer literals are supported.

```javascript
var 🐱 temperature meow -12
```

## If Statements

An `if` block must contain at least one statement.

```css
if x meowmeow 5 {
    x meow 6
}
```

## If / Else

The `else` clause is optional.

If present, the `else` block must also contain at least one statement.

```css
if x meowmeow 5 {
    x meow 6
} else {
    x meow 7
}
```

Nested `if` statements are supported:

```arduino
if x meowmeow 5 {
    if ready meowmeow true {
        x meow 10
    }
}
```

## Example Program

```javascript
let 🐈 limit meow 9000000000
var 🐱 count meow -5
var 😺 active meow true

if count woem 0 {
    count meow 10

    if active meowmeow true {
        active meow false
    }
} else {
    count meow 1
}
```

## Grammar

The complete EBNF grammar is stored in:

```
grammar.ebnf
```

The grammar describes every construct accepted by the parser.

## Lexer

The lexer:

- reads the source as UTF-8 bytes
- is implemented manually without regular expressions or lexer generators
- recognizes keywords, identifiers, integers, braces and emoji type names
- tracks line and column positions
- produces tokens containing:
  - token kind
  - original text
  - line
  - column

Lexical errors use the format:

```
compilation error: line L:C: message
```

## Parser

The parser is implemented using recursive descent.

It consumes the token stream using `peek` and `eat` operations and builds an Abstract Syntax Tree.

The main AST hierarchy contains:

```
ASTNode
├── ProgramNode
├── StmtNode
│   ├── VarDeclNode
│   ├── AssignmentNode
│   └── IfNode
└── ExprNode
    ├── IntegerLiteralNode
    ├── BooleanLiteralNode
    ├── IdentifierNode
    └── ComparisonNode
```

Each AST node stores its source position.

## Running the Compiler

Requirements:

```
Python 3
```

Run the compiler with:

```css
python3 compiler.py --ast input.txt
```

For example:

```
python3 compiler.py --ast tests/valid/full_program.txt
```

The program prints the generated AST.

Example:

```yaml
Program
  VarDecl
    mutable: true
    type: i32
    name: age
    value:
      IntegerLiteral value: 19
```

## Errors

Syntax and lexical errors are printed to `stderr`.

Example:

```
compilation error: line 1:14: unexpected character @
```

The compiler exits with a non-zero status and does not print an AST when an error occurs.

## Tests

The project contains at least:

- 15 valid programs
- 15 invalid programs
- expected AST output for valid programs
- expected error output for invalid programs

Tests are located in:

```bash
tests/valid/
tests/invalid/
```

Run all tests with:

```
./run_tests.sh
```

A successful run should end with:

```
=== SUMMARY ===
Passed: 30
Failed: 0
```

## Project Files

```
compiler.py
grammar.ebnf
README.md
ai_usage.txt
run_tests.sh
tests/
├── valid/
└── invalid/
```

## AI Usage

AI usage during development is documented separately in:

```
ai_usage.txt
```
