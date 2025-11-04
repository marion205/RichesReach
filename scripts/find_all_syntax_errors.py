#!/usr/bin/env python3
"""
Find ALL syntax errors in a Python file by attempting to parse incrementally.
"""
import ast
import sys

file_path = sys.argv[1] if len(sys.argv) > 1 else "backend/backend/final_complete_server.py"

with open(file_path, 'r') as f:
    lines = f.readlines()

print(f"Analyzing {file_path}...\n")
print("=" * 80)
print("ALL SYNTAX ERRORS:")
print("=" * 80)

errors = []
i = 0
max_iterations = 100  # Prevent infinite loop

while i < len(lines) and len(errors) < 100:
    try:
        # Try parsing from line i onwards
        code_to_test = ''.join(lines[i:])
        ast.parse(code_to_test)
        break  # Success - no more errors
    except SyntaxError as e:
        error_line = i + (e.lineno or 1) - 1
        if error_line < len(lines):
            # Avoid duplicates
            if not any(err[0] == error_line for err in errors):
                errors.append((
                    error_line + 1,
                    e.msg,
                    lines[error_line].rstrip()[:80] if error_line < len(lines) else ''
                ))
            i = error_line + 1
        else:
            break
    except Exception:
        break

if errors:
    print(f"\nFound {len(errors)} syntax error(s):\n")
    for idx, (line_num, msg, text) in enumerate(errors, 1):
        print(f"{idx:3d}. Line {line_num:5d}: {msg}")
        print(f"      Text: {repr(text)}")
        # Show context
        if line_num > 1 and line_num <= len(lines):
            print(f"      Context:")
            for ctx_line in range(max(0, line_num - 3), min(len(lines), line_num + 1)):
                marker = ">>>" if ctx_line == line_num - 1 else "   "
                print(f"      {marker} {ctx_line + 1:5d}: {lines[ctx_line].rstrip()[:70]}")
        print()
    print("=" * 80)
    print(f"\nTotal: {len(errors)} error(s) found")
else:
    print("\n✅ No syntax errors found!")

