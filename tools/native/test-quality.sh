#!/bin/bash
# test-quality.sh: the graphics quality presets (src/client_mp/cl_quality.h): mode choice by line count and the
# preset table's ranges, on the build host with a plain C++ compiler. No device or engine build needed.
R=$(cd "$(dirname "$0")/../.." && pwd)
OUT=$(mktemp -d)
${CXX:-g++} -std=c++17 -Wall -Wextra -o "$OUT/quality_test" "$R/android/test/quality_test.cpp" || exit 1
"$OUT/quality_test"
status=$?
rm -rf "$OUT"
exit $status
