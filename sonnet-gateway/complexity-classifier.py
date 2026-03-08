#!/usr/bin/env python3
"""
Sonnet-Gate v3 — Complexity Classifier
UserPromptSubmit hook (user-level, global across all projects).

Thay đổi so với v2:
  - Load patterns từ complexity-config.json (không cần edit .py)
  - additionalContext rõ ràng hơn, Claude tuân thủ tốt hơn
  - Thêm model_cost_estimate vào log
  - Thêm patterns tiếng Việt

Setup:
  chmod +x ~/.claude/hooks/complexity-classifier.py

Đăng ký trong ~/.claude/settings.json:
  {
    "hooks": {
      "UserPromptSubmit": [{
        "hooks": [{"type": "command",
                   "command": "python3 \\"$HOME/.claude/hooks/complexity-classifier.py\\"",
                   "timeout": 5}]
      }]
    }
  }

Test thủ công:
  echo '{"prompt": "fix typo in README", "session_id": "test"}' \\
    | python3 ~/.claude/hooks/complexity-classifier.py

  echo '{"prompt": "thiết kế lại hệ thống authentication với OAuth2", "session_id": "test"}' \\
    | python3 ~/.claude/hooks/complexity-classifier.py
"""
import sys
import json
import re
import os
from datetime import datetime
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
HOOKS_DIR   = Path.home() / ".claude" / "hooks"
CONFIG_PATH = HOOKS_DIR / "complexity-config.json"
LOG_DIR     = Path.home() / ".claude" / "logs" / "complexity-classifier"

# ── Fallback defaults (dùng khi config.json chưa tồn tại) ─────────────────────
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
        r"\b(thiết kế|kiến trúc|triển khai|tích hợp|di chuyển|tái cấu trúc)\b",
        r"\b(hệ thống|nền tảng|dịch vụ|hiệu suất|bảo mật|xác thực)\b",
    ],
    "cost_estimate_tokens": {"TRIVIAL": 0, "STANDARD": 4000, "COMPLEX": 12000},
}

# ── Config loader ──────────────────────────────────────────────────────────────
def load_config() -> dict:
    """Load từ JSON nếu tồn tại, fallback về DEFAULT_CONFIG."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                cfg = json.load(f)
            # Merge với defaults để tránh KeyError nếu config thiếu key
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
        except Exception:
            pass  # parse lỗi → fallback
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
PIPELINE_INSTRUCTIONS = {
    "TRIVIAL": (
        "🟢",
        "Sonnet-only. No Opus. No context-gathering phase.",
        (
            "✅ Current model (Sonnet) is optimal for this task.\n"
            "- Xử lý trực tiếp bằng Sonnet hiện tại\n"
            "- KHÔNG spawn subagent gather context\n"
            "- KHÔNG gọi Opus dưới bất kỳ hình thức nào\n"
            "- Target: trả lời trong ≤3 lượt tool calls"
        ),
    ),
    "STANDARD": (
        "🟡",
        "opusplan mode: Opus plans, Sonnet executes.",
        (
            "⚠️ RECOMMENDED: Switch to opusplan mode for better results.\n"
            "   User should run: /model opusplan\n"
            "   Or press: Shift+Tab → select 'opusplan'\n"
            "\n"
            "Pipeline khi dùng opusplan:\n"
            "- Opus xử lý plan phase → Sonnet thực thi code\n"
            "- Đây là balanced pipeline cho task vừa\n"
            "- Estimated cost: ~$0.02-0.05 per request"
        ),
    ),
    "COMPLEX": (
        "🔴",
        "Full pipeline: Sonnet gather → single Opus decision → Sonnet execute.",
        (
            "🚨 STRONGLY RECOMMENDED: Switch to Opus for complex tasks.\n"
            "   User should run: /model opus\n"
            "   Or press: Shift+Tab → select 'Opus'\n"
            "\n"
            "Pipeline khi dùng Opus:\n"
            "- Bước 1 (Sonnet subagent): Thu thập context, chạy bash exploration,\n"
            "  đọc files liên quan → ghi ra .claude/context-snapshot.md\n"
            "  KHÔNG sửa bất kỳ file nào trong bước này\n"
            "- Bước 2 (1 Opus request duy nhất): Đọc context-snapshot.md,\n"
            "  ra execution-plan.md với numbered task list rõ ràng\n"
            "  KHÔNG chạy bash hay đọc thêm file trong bước này\n"
            "- Bước 3 (Sonnet subagent): Thực thi theo plan, commit sau mỗi task,\n"
            "  ghi execution-report.md\n"
            "- Bước 4 (Opus, chỉ khi cần): Validate nếu có test failures hoặc\n"
            "  architectural mismatch\n"
            "- Estimated cost: ~$0.50 per request (flat rate)"
        ),
    ),
}

def build_context(result: dict) -> str:
    level  = result["level"]
    emoji, summary, instructions = PIPELINE_INSTRUCTIONS[level]
    cost   = result["cost_tokens"]
    cost_note = f"~{cost:,} Opus tokens" if cost > 0 else "0 Opus tokens (Sonnet only)"

    return (
        f"[SONNET-GATE: {level} {emoji}]\n"
        f"Pipeline: {summary}\n"
        f"Estimated cost: {cost_note}\n"
        f"\nBắt buộc tuân thủ:\n{instructions}\n"
        f"[/SONNET-GATE]"
    )

# ── Logger ─────────────────────────────────────────────────────────────────────
def log_entry(prompt: str, result: dict, session_id: str):
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
    except Exception:
        pass  # log failure không bao giờ cản luồng chính

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
        print("sonnet-gate classifier: invalid JSON input", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"sonnet-gate classifier error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
