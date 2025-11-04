#!/usr/bin/env python3

import re, sys, os, shutil, argparse

# --- CLI ---
p = argparse.ArgumentParser(description="Auto-indent under-indented field handlers inside the main try block.")
p.add_argument("file", help="Path to graphql endpoint file (e.g., backend/app/api/graphql.py)")
p.add_argument("--range", help="Optional line range start:end (1-based), e.g. 3610:3640", default=None)
args = p.parse_args()

FILE = args.file
range_start = range_end = None
if args.range:
    try:
        range_start, range_end = [int(x) for x in args.range.split(":")]
    except Exception:
        print("[!] --range must be like 3610:3640")
        sys.exit(2)

# Patterns
FUNC_PAT = re.compile(r'^\s*def\s+.*graphql.*\(', re.IGNORECASE)
TRY_PAT  = re.compile(r'^\s*try:\s*$')
EXC_PAT  = re.compile(r'^\s*(except|finally)\b')
# Catch more shapes:
#   if "foo" in fields:
#   elif "foo" in requested_fields:
#   if field == "foo":
#   elif field in {"a","b"}:
#   if ("foo" in fields) and ...
HANDLER_HEAD_PAT = re.compile(
    r'''^\s*(if|elif)\s+ # header
        (                 # any of:
           [^:]*\bin\s+\w+[^:]*     # ... in fields/list/set ...
         | [^:]*\bfield\s*==\s*['"][^'"]+['"][^:]*  # field == "foo"
         | [^:]*['"][^'"]+['"]\s+in\s+\w+[^:]*    # "foo" in something
        )\s*:\s*$''',
    re.VERBOSE
)

def leading_spaces(s: str) -> int:
    return len(s) - len(s.lstrip(' '))

def indent_line(lines, j, amount):
    if not lines[j].strip():
        # Keep blank lines aligned visually
        lines[j] = ' ' * (leading_spaces(lines[j]) + amount) + ''
    else:
        lines[j] = ' ' * (leading_spaces(lines[j]) + amount) + lines[j].lstrip()

def shift_block(lines, start_idx, amount):
    """Indent header line and its block by `amount` spaces, stopping when a line
    with indent <= header indent (sibling or outer) is encountered."""
    i = start_idx
    header_indent = leading_spaces(lines[i])
    indent_line(lines, i, amount)
    i += 1
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            indent_line(lines, i, amount)
            i += 1
            continue
        curr = leading_spaces(line)
        if curr <= header_indent:
            break
        indent_line(lines, i, amount)
        i += 1
    return i

with open(FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()

# 1) Find the graphql function (best-effort; fallback to whole file)
func_i = None
for i, ln in enumerate(lines):
    if FUNC_PAT.search(ln):
        func_i = i
        break

func_indent = leading_spaces(lines[func_i]) if func_i is not None else 0

# 2) Find the first try: one level deeper than the function (best-effort)
try_i = None
if func_i is not None:
    for i in range(func_i + 1, len(lines)):
        ln = lines[i]
        if ln.strip().startswith("def ") and leading_spaces(ln) <= func_indent:
            break  # hit next function
        if TRY_PAT.match(ln) and leading_spaces(ln) == func_indent + 4:
            try_i = i
            break

# If we can't detect the try (rare), just treat whole file as region with a default "desired" indent of 4
if try_i is None:
    print("[i] Could not locate canonical 'try:' inside graphql function; falling back to whole-file pass with desired indent = 4.")
    try_indent = 0
    try_body_indent = 4
    start_scan = 0
    end_scan = len(lines)
else:
    try_indent = leading_spaces(lines[try_i])
    try_body_indent = try_indent + 4
    # End of try-block is first except/finally at the same indent
    end_scan = len(lines)
    for i in range(try_i + 1, len(lines)):
        ln = lines[i]
        if EXC_PAT.match(ln) and leading_spaces(ln) == try_indent:
            end_scan = i
            break
    start_scan = try_i + 1

# Optional user-specified line-range clamp (1-based inclusive)
if range_start and range_end:
    # Convert to 0-based indices and clamp to [start_scan, end_scan)
    rs = max(start_scan, range_start - 1)
    re_ = min(end_scan, range_end)
    start_scan, end_scan = rs, re_

changes = 0
i = start_scan
while i < end_scan:
    ln = lines[i]
    m = HANDLER_HEAD_PAT.match(ln)
    if m:
        curr = leading_spaces(ln)
        if curr < try_body_indent:
            amount = try_body_indent - curr
            i = shift_block(lines, i, amount)
            changes += 1
            # continue without increment; i already moved
            continue
    i += 1

if not changes:
    print("[=] No under-indented handlers found in the target region. (No changes.)")
    sys.exit(0)

# Backup once
bak = FILE + ".bak"
if not os.path.exists(bak):
    shutil.copyfile(FILE, bak)

with open(FILE, "w", encoding="utf-8") as f:
    f.writelines(lines)

print(f"[✓] Indented {changes} handler block(s).")
print(f"[i] Backup saved at: {bak}")

