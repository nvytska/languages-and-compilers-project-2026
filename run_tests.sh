#!/bin/bash
set -eu

root_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
exec "${PYTHON:-python3}" -B "$root_dir/tests/run_tests.py" "$@"
