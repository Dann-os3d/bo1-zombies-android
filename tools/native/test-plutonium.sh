#!/bin/bash
# test-plutonium.sh: tools/native/import-plutonium.py on temporary folders, on the build host with Python 3 only.
R=$(cd "$(dirname "$0")/../.." && pwd)
python3 "$R/android/test/test_import_plutonium.py"
