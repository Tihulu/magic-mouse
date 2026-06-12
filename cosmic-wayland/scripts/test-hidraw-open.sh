#!/usr/bin/env bash
set -euo pipefail
PATH_TO_TEST="${1:-/dev/hidraw8}"
python3 - "$PATH_TO_TEST" <<'PY'
import os
import select
import sys
path = sys.argv[1]
print(f"Testing raw hidraw open: {path}")
print(f"readable={os.access(path, os.R_OK)} writable={os.access(path, os.W_OK)}")
try:
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
except Exception as exc:
    print(f"OPEN_FAILED: {type(exc).__name__}: {exc}")
    raise SystemExit(1)
print("OPEN_OK: move/swipe/touch the Magic Mouse for up to 10 seconds...")
end = __import__('time').time() + 10
count = 0
while __import__('time').time() < end:
    ready, _, _ = select.select([fd], [], [], 0.5)
    if not ready:
        continue
    data = os.read(fd, 128)
    if data:
        count += 1
        print(data.hex(' '), flush=True)
os.close(fd)
print(f"packets={count}")
PY
