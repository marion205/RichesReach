#!/usr/bin/env python3

"""
Auto-fix stray field handlers that must live inside the main try: block
of your GraphQL endpoint. It:
  - Locates the GraphQL endpoint function (name contains 'graphql')
  - Finds the first 'try:' inside that function
  - Ensures any top-level `if/elif "<field>" in fields:` handlers between
    that try and its matching except/finally are indented to the try-body level.

Backs up the original file as <file>.bak once before writing.
"""

import re, sys, os, shutil

FILE = sys.argv[1] if len(sys.argv) > 1 else "backend/app/api/graphql.py"
FUNC_PAT = re.compile(r'^\s*async\s+def\s+.*graphql.*\(|^\s*def\s+.*graphql.*\(', re.IGNORECASE)
TRY_PAT  = re.compile(r'^\s*try:\s*$')
EXC_PAT  = re.compile(r'^\s*(except|finally)\b')
HANDLER_PAT = re.compile(
    r'^\s*(if|elif)\s+([\'"]).+?\2\s+in\s+(requested_)?fields\s*:\s*$'
)

def leading_spaces(s: str) -> int:
    return len(s) - len(s.lstrip(' '))

def shift_block(lines, start_idx, amount):
    """Indent header line and its block by `amount` spaces, stopping when
    we reach a line with indent <= header indent (new block/sibling)."""
    i = start_idx
    header_indent = leading_spaces(lines[i])
    def indent_line(j):
        if lines[j].strip():
            lines[j] = ' ' * (leading_spaces(lines[j]) + amount) + lines[j].lstrip()
        else:
            # keep blank lines visually aligned
            lines[j] = ' ' * (leading_spaces(lines[j]) + amount) + ''
    # shift header
    indent_line(i); i += 1
    # shift block lines
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            indent_line(i); i += 1; continue
        curr = leading_spaces(line)
        # Stop at sibling/outer block boundary
        if curr <= header_indent:
            break
        indent_line(i); i += 1
    return i

with open(FILE, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1) Find the graphql function line
func_i = None
for i, ln in enumerate(lines):
    if FUNC_PAT.search(ln):
        func_i = i
        break
if func_i is None:
    print(f"[!] Could not find a function containing 'graphql' in {FILE}")
    sys.exit(1)

func_indent = leading_spaces(lines[func_i])

# 2) Find the first try: inside that function (one indent level deeper)
try_i = None
for i in range(func_i + 1, len(lines)):
    ln = lines[i]
    if (ln.strip().startswith("def ") or ln.strip().startswith("async def ")) and leading_spaces(ln) <= func_indent:
        break  # next top-level/peer def; give up
    if TRY_PAT.match(ln) and leading_spaces(ln) == func_indent + 4:
        try_i = i
        break

if try_i is None:
    print(f"[!] Could not find a 'try:' inside the graphql function.")
    sys.exit(1)

try_indent = leading_spaces(lines[try_i])
try_body_indent = try_indent + 4

# 3) Find where this try-block ends (except/finally at the same indent)
end_i = None
for i in range(try_i + 1, len(lines)):
    ln = lines[i]
    if EXC_PAT.match(ln) and leading_spaces(ln) == try_indent:
        end_i = i
        break
if end_i is None:
    # If we didn't find except/finally, treat file end as the boundary
    end_i = len(lines)

# 4) Walk the region and fix handlers with too-small indentation
i = try_i + 1
changes = 0
while i < end_i:
    ln = lines[i]
    m = HANDLER_PAT.match(ln)
    if m:
        curr = leading_spaces(ln)
        if curr < try_body_indent:
            amount = try_body_indent - curr
            i = shift_block(lines, i, amount)
            changes += 1
            # region moved, adjust end boundary (lines count unchanged, index advanced)
            continue
    i += 1

if not changes:
    print("[=] No handlers needed fixing. (Nothing changed.)")
    sys.exit(0)

# 5) Backup once and write
bak = FILE + ".bak"
if not os.path.exists(bak):
    shutil.copyfile(FILE, bak)
with open(FILE, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"[✓] Indented {changes} handler block(s).")
print(f"[i] Backup: {bak}")

