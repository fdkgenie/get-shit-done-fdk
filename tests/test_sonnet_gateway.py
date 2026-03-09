#!/usr/bin/env python3
"""
GSD Sonnet-Gateway — Comprehensive Test Suite
Tests for complexity classifier, archiver, and stats utilities.

Usage:
  python3 test_sonnet_gateway.py
  python3 test_sonnet_gateway.py -v  # verbose output
"""
import unittest
import json
import sys
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add hooks directory to path for imports
hooks_dir = Path(__file__).parent.parent / 'hooks'
sys.path.insert(0, str(hooks_dir))

# Import the modules we're testing using importlib (needed for hyphenated module names)
import importlib.util

def import_module_from_file(module_name: str, file_path: Path):
    """Dynamically import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module {module_name} from {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

try:
    # Import hyphenated Python modules using importlib
    classifier_module = import_module_from_file(
        'gsd_complexity_classifier',
        hooks_dir / 'gsd-complexity-classifier.py'
    )
    archive_module = import_module_from_file(
        'gsd_archive_files',
        hooks_dir / 'gsd-archive-files.py'
    )
    stats_module = import_module_from_file(
        'gsd_stats',
        hooks_dir / 'gsd-stats.py'
    )

    # Extract functions we need
    classify = classifier_module.classify
    build_context = classifier_module.build_context
    load_config = classifier_module.load_config
    should_watch = archive_module.should_watch
    archive_file = archive_module.archive_file
    load_logs = stats_module.load_logs
    format_cost = stats_module.format_cost

except ImportError as e:
    print(f"Error: Could not import all modules: {e}")
    print("Tests will fail. Ensure hooks are in the correct location.")
    sys.exit(1)


class TestComplexityClassifier(unittest.TestCase):
    """Test suite for complexity classifier."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "word_thresholds": {"trivial_max": 10, "complex_min": 60, "complex_boost": 100},
            "trivial_patterns": [
                r"\b(fix typo|rename|format|lint)\b",
                r"\b(add comment|update comment)\b",
                r"\b(git (status|log|diff|add|commit|push|stash|pull|fetch))\b",
            ],
            "standard_patterns": [
                r"\b(implement|add|create|write).{0,30}(function|method|class|component|test|util|validation)\b",
                r"\b(fix|debug|resolve).{0,30}(bug|error|issue|warning)\b",
            ],
            "complex_patterns": [
                r"\b(architect|design|redesign|overhaul|restructure)\b",
                r"\b(migrate|migration|upgrade).{0,30}(database|framework|version|stack|api|rest|graphql|microservice)\b",
                r"\b(refactor).{0,20}(entire|whole|all|codebase|module)\b",
                r"\b(entire|whole).{0,30}(rest|api|system|codebase|service)\b",
                r"\b(rest\s+api|graphql|microservice|microservices|authentication system)\b",
                r"\b(migrate.{0,30}to|migration.{0,30}to)\b",
            ],
            "cost_estimate_tokens": {"TRIVIAL": 0, "STANDARD": 4000, "COMPLEX": 12000},
        }

    def test_trivial_classification(self):
        """Test TRIVIAL complexity classification."""
        prompts = [
            "fix typo in README",
            "rename variable x to y",
            "git status",
            "format code",
        ]
        for prompt in prompts:
            result = classify(prompt, self.config)
            self.assertEqual(result["level"], "TRIVIAL",
                           f"Expected TRIVIAL for: {prompt}")
            self.assertEqual(result["cost_tokens"], 0)

    def test_standard_classification(self):
        """Test STANDARD complexity classification."""
        prompts = [
            "implement user login function",
            "add validation to email field",
            "fix bug in payment processing",
            "debug error in API endpoint",
        ]
        for prompt in prompts:
            result = classify(prompt, self.config)
            self.assertEqual(result["level"], "STANDARD",
                           f"Expected STANDARD for: {prompt}")
            self.assertEqual(result["cost_tokens"], 4000)

    def test_complex_classification(self):
        """Test COMPLEX complexity classification."""
        prompts = [
            "migrate entire REST API to GraphQL",
            "architect new microservices platform",
            "refactor entire codebase to TypeScript",
            "redesign and restructure authentication system",
        ]
        for prompt in prompts:
            result = classify(prompt, self.config)
            self.assertEqual(result["level"], "COMPLEX",
                           f"Expected COMPLEX for: {prompt}, got {result['level']} with scores {result['scores']}")
            self.assertEqual(result["cost_tokens"], 12000)

    def test_word_count_influence(self):
        """Test that word count influences classification."""
        # Short prompt should lean TRIVIAL
        short = "update"
        result_short = classify(short, self.config)

        # Long prompt (>100 words) should boost COMPLEX score
        long = " ".join(["word"] * 120)
        result_long = classify(long, self.config)

        # Scores should differ based on word count
        self.assertNotEqual(result_short["scores"]["words"],
                          result_long["scores"]["words"])

    def test_build_context_output(self):
        """Test context building for each complexity level."""
        for level in ["TRIVIAL", "STANDARD", "COMPLEX"]:
            result = {"level": level, "cost_tokens": 0}
            context = build_context(result)

            # Verify expected patterns in context
            self.assertIn("[GSD-SONNET-GATE:", context)
            self.assertIn(level, context)
            self.assertIn("Recommended approach:", context)


class TestArchiveFiles(unittest.TestCase):
    """Test suite for file archiver."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

        # Create test planning directory
        self.planning_dir = self.project_dir / ".planning"
        self.planning_dir.mkdir()

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_should_watch_match(self):
        """Test pattern matching for watched files."""
        patterns = [".planning/**/PLAN.md", ".planning/STATE.md"]

        # Should match
        test_file = self.project_dir / ".planning" / "phase-1" / "PLAN.md"
        self.assertTrue(should_watch(test_file, self.project_dir, patterns))

        test_file2 = self.project_dir / ".planning" / "STATE.md"
        self.assertTrue(should_watch(test_file2, self.project_dir, patterns))

    def test_should_watch_no_match(self):
        """Test that non-watched files aren't matched."""
        patterns = [".planning/**/PLAN.md"]

        # Should not match
        test_file = self.project_dir / "README.md"
        self.assertFalse(should_watch(test_file, self.project_dir, patterns))

    def test_archive_file_creation(self):
        """Test archive file creation."""
        # Create source file
        src_file = self.planning_dir / "TEST.md"
        src_file.write_text("test content")

        # Create archive
        archive_dir = self.project_dir / ".claude" / "archive"
        result = archive_file(src_file, archive_dir, "pre")

        # Verify archive was created
        self.assertIsNotNone(result)
        self.assertTrue(Path(result).exists())
        self.assertTrue(Path(result).name.startswith("TEST-"))
        self.assertTrue(Path(result).name.endswith("-pre.md"))

    def test_archive_nonexistent_file(self):
        """Test archiving nonexistent file returns None."""
        nonexistent = self.planning_dir / "DOESNOTEXIST.md"
        archive_dir = self.project_dir / ".claude" / "archive"

        result = archive_file(nonexistent, archive_dir, "post")
        self.assertIsNone(result)


class TestStats(unittest.TestCase):
    """Test suite for stats utilities."""

    def test_format_cost(self):
        """Test cost formatting."""
        # Test various token amounts
        self.assertEqual(format_cost(0), "~0 tokens (~$0.0000)")
        self.assertEqual(format_cost(4000), "~4,000 tokens (~$0.0200)")
        self.assertEqual(format_cost(12000), "~12,000 tokens (~$0.0600)")
        self.assertEqual(format_cost(1000000), "~1,000,000 tokens (~$5.0000)")

    def test_load_logs_empty(self):
        """Test loading logs from nonexistent directory."""
        # This should return empty list without error
        logs = load_logs(filter_today=False)
        self.assertIsInstance(logs, list)


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflow."""

    def test_classifier_pipeline(self):
        """Test complete classification pipeline."""
        config = {
            "word_thresholds": {"trivial_max": 10, "complex_min": 60, "complex_boost": 100},
            "trivial_patterns": [r"\b(fix typo)\b"],
            "standard_patterns": [r"\b(implement)\b"],
            "complex_patterns": [
                r"\b(migrate|migration)\b",
                r"\b(entire|whole)\b",
                r"\b(system|api|codebase)\b"
            ],
            "cost_estimate_tokens": {"TRIVIAL": 0, "STANDARD": 4000, "COMPLEX": 12000},
        }

        test_cases = [
            ("fix typo", "TRIVIAL", 0),
            ("implement feature", "STANDARD", 4000),
            ("migrate entire system", "COMPLEX", 12000),
        ]

        for prompt, expected_level, expected_cost in test_cases:
            result = classify(prompt, config)
            context = build_context(result)

            self.assertEqual(result["level"], expected_level,
                           f"Expected {expected_level} for '{prompt}', got {result['level']} with scores {result['scores']}")
            self.assertEqual(result["cost_tokens"], expected_cost)
            self.assertIn(expected_level, context)


def run_tests():
    """Run all tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestComplexityClassifier))
    suite.addTests(loader.loadTestsFromTestCase(TestArchiveFiles))
    suite.addTests(loader.loadTestsFromTestCase(TestStats))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2 if '-v' in sys.argv else 1)
    result = runner.run(suite)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
