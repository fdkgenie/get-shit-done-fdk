#!/usr/bin/env python3
"""
GSD Sonnet-Gateway — Complexity Classifier
UserPromptSubmit hook for GSD (Get Shit Done).

Python version: Requires Python 3.7+ (uses pathlib, typing, f-strings)

Integration with GSD's existing workflow:
  - Classifies prompts as TRIVIAL/STANDARD/COMPLEX
  - Recommends appropriate GSD profiles (sonnet-direct, opusplan, opus-full)
  - Logs classifications for audit trail
  - Integrates with GSD's statusline for real-time visibility

Setup:
  chmod +x ~/.claude/hooks/gsd-complexity-classifier.py

Register in ~/.claude/settings.json:
  {
    "hooks": {
      "UserPromptSubmit": [{
        "hooks": [{"type": "command",
                   "command": "python3 \"$HOME/.claude/hooks/gsd-complexity-classifier.py\"",
                   "timeout": 5}]
      }]
    }
  }

Test manually:
  echo '{"prompt": "fix typo in README", "session_id": "test"}' \\
    | python3 ~/.claude/hooks/gsd-complexity-classifier.py

  echo '{"prompt": "migrate entire REST API to GraphQL", "session_id": "test"}' \\
    | python3 ~/.claude/hooks/gsd-complexity-classifier.py
"""
import sys
import json
import re
import os
from datetime import datetime
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
HOOKS_DIR   = Path.home() / ".claude" / "hooks"
CONFIG_PATH = HOOKS_DIR / "gsd-complexity-config.json"
LOG_DIR     = Path.home() / ".claude" / "logs" / "gsd-complexity-classifier"

# ── Fallback defaults (used when config.json doesn't exist) ───────────────────
DEFAULT_CONFIG = {
    "word_thresholds": {"trivial_max": 10, "complex_min": 60, "complex_boost": 100},
    "trivial_patterns": [
        r"\b(fix typo|rename|format|lint|add comment|update comment)\b",
        r"\b(git (status|log|diff|add|commit|push|stash|pull|fetch))\b",
        r"^(ls|cat|find|grep|echo|pwd|cd|which|type)\b",
        r"\b(what is|explain|describe|show me)\b.{0,40}(variable|function|file|line|class)",
        r"\b(simple|quick|small|tiny|minor)\b.{0,20}(fix|change|edit|update)",
        r"\b(add (a )?(line|comment|import|export|log|print))\b",
        r"\b(remove (a )?(line|comment|import|log|print))\b",
        r"\b(rename (file|variable|function|class|method))\b",
    ],
    "standard_patterns": [
        r"\b(implement|add|create|write).{0,30}(function|method|class|component|test|util)\b",
        r"\b(fix|debug|resolve).{0,30}(bug|error|issue|warning)\b",
        r"\b(update|modify|change).{0,30}(logic|behavior|config|setting)\b",
        r"\b(refactor)\b.{0,30}(function|method|class|module)\b",
    ],
    "complex_patterns": [
        r"\b(architect|design|redesign|overhaul|restructure)\b",
        r"\b(implement|build|create).{0,30}(system|service|pipeline|api|platform|framework)\b",
        r"\b(refactor).{0,20}(entire|whole|all|codebase|module)\b",
        r"\b(migrate|migration|upgrade).{0,30}(database|framework|version|stack)\b",
        r"\b(multi.?file|codebase.?wide|across.{0,10}files?|multiple.{0,10}files?)\b",
        r"\b(performance|optimize|scale|security|authentication|authorization)\b",
        r"\b(investigate|diagnose|trace|profile)\b",
        r"\b(integrate|orchestrat|coordinat)\b",
        r"\b(plan|strategy|approach|solution)\b.{0,10}(for|to)\b",
    ],
    "cost_estimate_tokens": {"TRIVIAL": 0, "STANDARD": 4000, "COMPLEX": 12000},
    "watched_files": [
        ".planning/**/PLAN.md",
        ".planning/**/SUMMARY.md",
        ".planning/**/RESEARCH.md",
        ".planning/STATE.md",
    ],
    "gitignore_entries": [
        ".claude/archive/",
        ".claude/logs/gsd-complexity-classifier/",
    ],
}

# ── Config loader ──────────────────────────────────────────────────────────────
def load_config() -> dict:
    """Load from JSON if exists, fallback to DEFAULT_CONFIG."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                cfg = json.load(f)
            # Merge with defaults to avoid KeyError if config is missing keys
            merged = {**DEFAULT_CONFIG, **cfg}
            merged["word_thresholds"] = {
                **DEFAULT_CONFIG["word_thresholds"],
                **cfg.get("word_thresholds", {}),
            }
            merged["cost_estimate_tokens"] = {
                **DEFAULT_CONFIG["cost_estimate_tokens"],
                **cfg.get("cost_estimate_tokens", {}),
            }
            return merged
        except (json.JSONDecodeError, OSError, KeyError) as e:
            # Log parse error but continue with defaults
            print(f"[gsd-classifier] Warning: Could not load config from {CONFIG_PATH}: {e}", file=sys.stderr)
    return DEFAULT_CONFIG

# ── Classifier ─────────────────────────────────────────────────────────────────
def classify(prompt: str, config: dict) -> dict:
    prompt_lower = prompt.lower().strip()
    word_count   = len(prompt.split())
    thresholds   = config["word_thresholds"]

    def score(patterns):
        return sum(1 for p in patterns if re.search(p, prompt_lower))

    trivial_score  = score(config["trivial_patterns"])
    standard_score = score(config["standard_patterns"])
    complex_score  = score(config["complex_patterns"])

    # Word count adjustments
    if word_count > thresholds["complex_boost"]:
        complex_score += 2
    elif word_count > thresholds["complex_min"]:
        complex_score += 1
    elif word_count < thresholds["trivial_max"]:
        trivial_score += 1

    # Decision
    if trivial_score > 0 and complex_score == 0 and standard_score == 0:
        level = "TRIVIAL"
    elif complex_score >= 2 or (complex_score >= 1 and word_count > thresholds["complex_min"]):
        level = "COMPLEX"
    else:
        level = "STANDARD"

    cost_tokens = config["cost_estimate_tokens"].get(level, 0)

    return {
        "level": level,
        "cost_tokens": cost_tokens,
        "scores": {
            "trivial": trivial_score,
            "standard": standard_score,
            "complex": complex_score,
            "words": word_count,
        },
    }

# ── Context builder ────────────────────────────────────────────────────────────
GSD_PROFILE_INSTRUCTIONS = {
    "TRIVIAL": (
        "🟢",
        "Sonnet-only direct execution",
        (
            "✅ Current model (Sonnet) is optimal for this task.\n"
            "- Execute directly with Sonnet\n"
            "- NO subagent context gathering needed\n"
            "- NO Opus invocation required\n"
            "- Target: Complete in ≤3 tool calls\n"
            "- GSD Profile: sonnet-direct (if using /gsd:quick)"
        ),
    ),
    "STANDARD": (
        "🟡",
        "OpusPlan mode recommended: Opus plans, Sonnet executes",
        (
            "⚠️ RECOMMENDED: Use GSD with opusplan profile for better results.\n"
            "   Consider: /gsd:quick --discuss for structured approach\n"
            "   Or: /model opusplan for balanced execution\n"
            "\n"
            "Pipeline with opusplan:\n"
            "- Opus handles planning phase → Sonnet executes implementation\n"
            "- Balanced approach for medium complexity tasks\n"
            "- Estimated cost: ~$0.02-0.05 per request\n"
            "- GSD Profile: opusplan (balanced quality/cost)"
        ),
    ),
    "COMPLEX": (
        "🔴",
        "Full GSD orchestration: Multi-phase with Opus-led planning",
        (
            "🚨 STRONGLY RECOMMENDED: Use full GSD workflow for complex tasks.\n"
            "   Best approach: /gsd:plan-phase or /gsd:new-project\n"
            "   Alternative: /model opus for single-shot complex work\n"
            "\n"
            "GSD Multi-phase Pipeline:\n"
            "- Phase 1 (Opus): Research domain and analyze requirements\n"
            "- Phase 2 (Opus): Create detailed execution plan with task breakdown\n"
            "- Phase 3 (Sonnet): Execute in parallel waves with checkpoints\n"
            "- Phase 4 (Sonnet/Opus): Automated verification and validation\n"
            "- Estimated cost: ~$0.30-0.80 per phase\n"
            "- GSD Profile: opus-full (maximum quality, orchestrated execution)"
        ),
    ),
}

def build_context(result: dict) -> str:
    level  = result["level"]
    emoji, summary, instructions = GSD_PROFILE_INSTRUCTIONS[level]
    cost   = result["cost_tokens"]
    cost_note = f"~{cost:,} Opus tokens" if cost > 0 else "0 Opus tokens (Sonnet only)"

    return (
        f"[GSD-SONNET-GATE: {level} {emoji}]\n"
        f"Complexity: {summary}\n"
        f"Estimated cost: {cost_note}\n"
        f"\nRecommended approach:\n{instructions}\n"
        f"[/GSD-SONNET-GATE]"
    )

# ── Logger ─────────────────────────────────────────────────────────────────────
def log_entry(prompt: str, result: dict, session_id: str):
    """Log classification entry to daily log file."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        today    = datetime.now().strftime("%Y-%m-%d")
        log_file = LOG_DIR / f"classifications-{today}.jsonl"
        entry = {
            "ts":             datetime.now().isoformat(),
            "session_id":     session_id,
            "project":        os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd(),
            "level":          result["level"],
            "cost_tokens":    result["cost_tokens"],
            "scores":         result["scores"],
            "prompt_preview": prompt[:120] + ("…" if len(prompt) > 120 else ""),
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except (OSError, TypeError, ValueError) as e:
        # log failure never blocks main flow
        print(f"[gsd-classifier] Warning: Could not write log entry: {e}", file=sys.stderr)

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    try:
        data       = json.loads(sys.stdin.read())
        prompt     = data.get("prompt", "")
        session_id = data.get("session_id", "unknown")

        config = load_config()
        result = classify(prompt, config)
        log_entry(prompt, result, session_id)

        print(json.dumps({"additionalContext": build_context(result)}))
        sys.exit(0)

    except json.JSONDecodeError:
        print("gsd-sonnet-gate classifier: invalid JSON input", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"gsd-sonnet-gate classifier error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
