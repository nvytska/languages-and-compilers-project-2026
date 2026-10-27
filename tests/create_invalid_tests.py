from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent
ERR_DIR = ROOT / "err"

TESTS = {
    "literal_overflow": (
        """
        var 🐈 x meow 9223372036854775808
        """,
        "compilation error: line 1:14: "
        "integer constant 9223372036854775808 does not fit in i64",
    ),

    "narrowing_i64_to_i32": (
        """
        var 🐱 x meow 3000000000
        """,
        "compilation error: line 1:1: "
        "cannot initialize 'x' of type 'i32' "
        "with value of type 'i64'",
    ),

    "bool_arithmetic": (
        """
        var 🐱 x meow true + 1
        """,
        "compilation error: line 1:19: "
        "operator '+' requires integer operands",
    ),

    "bool_integer_compare": (
        """
        var 😺 x meow true meowmeow 1
        """,
        "compilation error: line 1:19: "
        "cannot compare 'bool' with 'i32'",
    ),

    "undeclared_variable": (
        """
        var 🐱 x meow y
        """,
        "compilation error: line 1:14: "
        "unknown name 'y'",
    ),

    "duplicate_local": (
        """
        murr f() kss 🐱 {
            var 🐱 x meow 1
            var 🐱 x meow 2
            mi x
        }
        """,
        "compilation error: line 3:5: "
        "'x' is already declared in this scope",
    ),

    "assign_to_const": (
        """
        let 🐱 x meow 1
        x meow 2
        """,
        "compilation error: line 2:1: "
        "cannot assign to constant 'x'",
    ),

    "if_condition_not_bool": (
        """
        if 1 {
            var 🐱 x meow 1
        }
        """,
        "compilation error: line 1:4: "
        "if condition must be bool, got 'i32'",
    ),

    "unknown_function": (
        """
        var 🐱 x meow missing()
        """,
        "compilation error: line 1:14: "
        "unknown function 'missing'",
    ),

    "function_too_few_args": (
        """
        murr add(🐱 a, 🐱 b) kss 🐱 {
            mi a + b
        }

        var 🐱 x meow add(1)
        """,
        "compilation error: line 5:14: "
        "function 'add' expects 2 arguments, got 1",
    ),

    "function_too_many_args": (
        """
        murr add(🐱 a, 🐱 b) kss 🐱 {
            mi a + b
        }

        var 🐱 x meow add(1, 2, 3)
        """,
        "compilation error: line 5:14: "
        "function 'add' expects 2 arguments, got 3",
    ),

    "function_wrong_arg_type": (
        """
        murr add(🐱 a, 🐱 b) kss 🐱 {
            mi a + b
        }

        var 🐱 x meow add(true, 2)
        """,
        "compilation error: line 5:18: "
        "argument 1 of function 'add' must have type "
        "'i32', got 'bool'",
    ),

    "wrong_return_type": (
        """
        murr bad() kss 🐱 {
            mi true
        }
        """,
        "compilation error: line 2:5: "
        "function must return 'i32', got 'bool'",
    ),

    "missing_return_path": (
        """
        murr f() kss 🐱 {
            if true {
                mi 1
            }
        }
        """,
        "compilation error: line 1:1: "
        "function 'f' may finish without mi",
    ),

    "constructor_too_few_values": (
        """
        mewi Point {
            var 🐱 x
            var 🐱 y
        }
        var Point p meow Point{10}
        """,
        "compilation error: line 5:18: "
        "structure 'Point' expects 2 values, got 1",
    ),

    "constructor_wrong_type": (
        """
        mewi Point {
            var 🐱 x
        }
        var Point p meow Point{true}
        """,
        "compilation error: line 4:24: "
        "field 'x' of structure 'Point' requires type "
        "'i32', got 'bool'",
    ),

    "unknown_field": (
        """
        mewi Point {
            var 🐱 x
        }
        var Point p meow Point{10}
        var 🐱 y meow p.z
        """,
        "compilation error: line 5:16: "
        "structure 'Point' has no field 'z'",
    ),

    "constant_field_chain": (
        """
        mewi Point {
            var 🐱 x
        }
        mewi Circle {
            let Point center
        }
        var Circle c meow Circle{Point{10}}
        c.center.x meow 20
        """,
        "compilation error: line 8:3: "
        "cannot assign through constant field 'center'",
    ),

    "mutating_method_on_const_object": (
        """
        mewi Point {
            var 🐱 x

            murr setX(🐱 value) kss 🐱 {
                x meow value
                mi x
            }
        }
        let Point p meow Point{10}
        p.setX(20)
        """,
        "compilation error: line 10:1: "
        "cannot call mutating member function "
        "on constant 'p'",
    ),

    "unknown_method": (
        """
        mewi Point {
            var 🐱 x
        }
        var Point p meow Point{10}
        p.nope()
        """,
        "compilation error: line 5:3: "
        "structure 'Point' has no member function 'nope'",
    ),

    "member_wrong_arg_count": (
        """
        mewi Point {
            var 🐱 x

            murr setX(🐱 value) kss 🐱 {
                x meow value
                mi x
            }
        }
        var Point p meow Point{10}
        p.setX()
        """,
        "compilation error: line 10:3: "
        "member function 'setX' expects 1 arguments, got 0",
    ),

    "duplicate_field": (
        """
        mewi Point {
            var 🐱 x
            var 🐱 x
        }
        """,
        "compilation error: line 3:5: "
        "field 'x' is already declared in structure 'Point'",
    ),
}


def main():
    ERR_DIR.mkdir(parents=True, exist_ok=True)
    for name, (source, expected) in TESTS.items():
        source = dedent(source).strip() + "\n"
        expected = expected + "\n"

        (ERR_DIR / f"{name}.txt").write_text(
            source,
            encoding="utf-8",
        )

        (ERR_DIR / f"{name}.expected").write_text(
            expected,
            encoding="utf-8",
        )


    print(f"Created {len(TESTS)} invalid tests in {ERR_DIR}")


if __name__ == "__main__":
    main()
