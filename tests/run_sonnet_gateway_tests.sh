#!/usr/bin/env bash
# GSD Sonnet-Gateway Test Runner
# Simple test runner that validates the hooks work correctly

set -e

HOOKS_DIR="$(dirname "$0")/../hooks"
TESTS_PASSED=0
TESTS_FAILED=0

echo "=================================================="
echo "  GSD Sonnet-Gateway Test Suite"
echo "=================================================="
echo ""

# Test 1: Complexity Classifier - TRIVIAL
echo "Test 1: Complexity Classifier - TRIVIAL prompt"
RESULT=$(echo '{"prompt": "fix typo in README", "session_id": "test"}' | python3 "$HOOKS_DIR/gsd-complexity-classifier.py")
if echo "$RESULT" | grep -q "TRIVIAL"; then
    echo "✅ PASSED - Correctly classified as TRIVIAL"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo "❌ FAILED - Expected TRIVIAL classification"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 2: Complexity Classifier - STANDARD
echo "Test 2: Complexity Classifier - STANDARD prompt"
RESULT=$(echo '{"prompt": "implement user login function", "session_id": "test"}' | python3 "$HOOKS_DIR/gsd-complexity-classifier.py")
if echo "$RESULT" | grep -q "STANDARD"; then
    echo "✅ PASSED - Correctly classified as STANDARD"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo "❌ FAILED - Expected STANDARD classification"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 3: Complexity Classifier - COMPLEX
echo "Test 3: Complexity Classifier - COMPLEX prompt"
RESULT=$(echo '{"prompt": "migrate entire REST API to GraphQL with schema and resolvers", "session_id": "test"}' | python3 "$HOOKS_DIR/gsd-complexity-classifier.py")
if echo "$RESULT" | grep -q "COMPLEX"; then
    echo "✅ PASSED - Correctly classified as COMPLEX"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo "❌ FAILED - Expected COMPLEX classification"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 4: Config file loading
echo "Test 4: Configuration file loading"
if [ -f "$HOOKS_DIR/gsd-complexity-config.json" ]; then
    if python3 -m json.tool "$HOOKS_DIR/gsd-complexity-config.json" > /dev/null 2>&1; then
        echo "✅ PASSED - Configuration file is valid JSON"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAILED - Configuration file is invalid JSON"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    echo "⚠️  SKIPPED - Configuration file not found"
fi
echo ""

# Test 5: Hooks are executable
echo "Test 5: Hooks are executable"
ALL_EXECUTABLE=true
for hook in gsd-complexity-classifier.py gsd-archive-files.py gsd-stats.py; do
    if [ ! -x "$HOOKS_DIR/$hook" ]; then
        echo "❌ FAILED - $hook is not executable"
        ALL_EXECUTABLE=false
    fi
done
if [ "$ALL_EXECUTABLE" = true ]; then
    echo "✅ PASSED - All hooks are executable"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 6: Stats utility basic functionality
echo "Test 6: Stats utility basic functionality"
if python3 "$HOOKS_DIR/gsd-stats.py" > /dev/null 2>&1; then
    echo "✅ PASSED - Stats utility runs without errors"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo "❌ FAILED - Stats utility encountered errors"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Summary
echo "=================================================="
echo "  Test Results"
echo "=================================================="
echo "Passed: $TESTS_PASSED"
echo "Failed: $TESTS_FAILED"
echo "Total:  $((TESTS_PASSED + TESTS_FAILED))"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo "✅ All tests passed!"
    exit 0
else
    echo "❌ Some tests failed"
    exit 1
fi
