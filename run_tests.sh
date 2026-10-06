#!/bin/bash

passed=0
failed=0

echo "=== VALID TESTS ==="

for f in tests/valid/*.txt; do
    expected="${f%.txt}.expected"

    actual="$(python3 compiler.py --ast "$f" 2>&1)"
    exit_code=$?
    wanted="$(cat "$expected")"

    if [ "$exit_code" -eq 0 ] && [ "$actual" = "$wanted" ]; then
        echo "PASS $f"
        passed=$((passed + 1))
    else
        echo "FAIL $f"
        echo "  expected exit: 0"
        echo "  actual exit:   $exit_code"
        echo "  expected:"
        echo "$wanted"
        echo "  actual:"
        echo "$actual"
        failed=$((failed + 1))
    fi
done


echo
echo "=== INVALID TESTS ==="

for f in tests/invalid/*.txt; do
    expected="${f%.txt}.expected"

    actual="$(python3 compiler.py --ast "$f" 2>&1)"
    exit_code=$?
    wanted="$(cat "$expected")"

    if [ "$exit_code" -ne 0 ] && [ "$actual" = "$wanted" ]; then
        echo "PASS $f"
        passed=$((passed + 1))
    else
        echo "FAIL $f"
        echo "  expected exit: non-zero"
        echo "  actual exit:   $exit_code"
        echo "  expected:"
        echo "$wanted"
        echo "  actual:"
        echo "$actual"
        failed=$((failed + 1))
    fi
done


echo
echo "=== SUMMARY ==="
echo "Passed: $passed"
echo "Failed: $failed"

if [ "$failed" -ne 0 ]; then
    exit 1
fi

exit 0
