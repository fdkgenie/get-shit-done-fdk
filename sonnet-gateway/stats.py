#!/usr/bin/env python3
"""
Sonnet-Gate v3 — Audit & Stats
Standalone script để xem log hậu kiểm và diff archive files.

Usage:
  python3 ~/.claude/hooks/stats.py               # stats tất cả logs
  python3 ~/.claude/hooks/stats.py today         # chỉ hôm nay
  python3 ~/.claude/hooks/stats.py diff          # diff 2 archive files mới nhất
  python3 ~/.claude/hooks/stats.py list <project># list archive files của project

Shortcut alias (thêm vào ~/.zshrc hoặc ~/.bashrc):
  alias sg-stats='python3 ~/.claude/hooks/stats.py'
  alias sg-diff='python3 ~/.claude/hooks/stats.py diff'
"""
import sys
import json
import os
import subprocess
from datetime import datetime, date
from pathlib import Path
from collections import Counter, defaultdict

LOG_DIR = Path.home() / ".claude" / "logs" / "complexity-classifier"

# ── Helpers ────────────────────────────────────────────────────────────────────
def load_logs(filter_today: bool = False) -> list[dict]:
    if not LOG_DIR.exists():
        return []
    entries = []
    for log_file in sorted(LOG_DIR.glob("classifications-*.jsonl")):
        if filter_today:
            today_str = date.today().strftime("%Y-%m-%d")
            if today_str not in log_file.name:
                continue
        try:
            with open(log_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entries.append(json.loads(line))
        except Exception:
            pass
    return entries

def format_cost(tokens: int) -> str:
    # Giá tham khảo Opus 4.6: $5/1M input tokens
    usd = tokens * 5 / 1_000_000
    return f"~{tokens:,} tokens (~${usd:.4f})"

# ── Stats command ──────────────────────────────────────────────────────────────
def cmd_stats(filter_today: bool = False):
    entries = load_logs(filter_today)
    if not entries:
        label = "today" if filter_today else "all time"
        print(f"No classification logs found ({label}).")
        return

    label     = "Today" if filter_today else "All time"
    total     = len(entries)
    counts    = Counter(e["level"] for e in entries)
    by_proj   = defaultdict(Counter)
    total_tok = sum(e.get("cost_tokens", 0) for e in entries)

    for e in entries:
        proj = Path(e.get("project", "unknown")).name
        by_proj[proj][e["level"]] += 1

    print(f"\n{'='*55}")
    print(f"  Sonnet-Gate Stats — {label}  ({total} prompts)")
    print(f"{'='*55}")

    emojis = {"TRIVIAL": "🟢", "STANDARD": "🟡", "COMPLEX": "🔴"}
    for level in ("TRIVIAL", "STANDARD", "COMPLEX"):
        count = counts.get(level, 0)
        pct   = 100 * count // total if total else 0
        bar   = "█" * (pct // 5)
        print(f"  {emojis[level]} {level:<10} {count:>4} ({pct:>3}%)  {bar}")

    print(f"\n  Total estimated Opus cost: {format_cost(total_tok)}")

    if len(by_proj) > 1:
        print(f"\n  By project:")
        for proj, proj_counts in sorted(by_proj.items()):
            proj_total = sum(proj_counts.values())
            c_count    = proj_counts.get("COMPLEX", 0)
            print(f"    {proj:<30} {proj_total:>4} prompts  "
                  f"({c_count} complex)")

    # Tìm 5 COMPLEX prompts gần nhất để review
    complex_entries = [e for e in entries if e["level"] == "COMPLEX"][-5:]
    if complex_entries:
        print(f"\n  Last {len(complex_entries)} COMPLEX prompts:")
        for e in reversed(complex_entries):
            ts   = e.get("ts", "")[:16]
            proj = Path(e.get("project", "")).name
            prev = e.get("prompt_preview", "")
            print(f"    [{ts}] [{proj}] {prev}")

    print(f"{'='*55}\n")

# ── Diff command ───────────────────────────────────────────────────────────────
def cmd_diff(project_dir: Path | None = None):
    """Diff 2 phiên bản mới nhất của bất kỳ watched file nào trong archive."""
    if project_dir is None:
        project_dir = Path.cwd()

    archive_dir = project_dir / ".claude" / "archive"
    if not archive_dir.exists():
        print(f"No archive directory found at: {archive_dir}")
        return

    # Group files theo stem gốc (e.g. "execution-plan")
    groups: dict[str, list[Path]] = defaultdict(list)
    for f in sorted(archive_dir.glob("*.md")):
        # Tên format: stem-YYYYMMDD-HHMMSS-phase.md
        # Lấy stem gốc bằng cách bỏ suffix timestamp
        parts = f.stem.rsplit("-", 3)  # tách tối đa 3 phần từ phải
        if len(parts) >= 2:
            base = parts[0]
            groups[base].append(f)

    if not groups:
        print(f"No archive files found in: {archive_dir}")
        return

    for base, files in sorted(groups.items()):
        if len(files) < 2:
            continue
        oldest, newest = files[0], files[-1]
        print(f"\n{'─'*55}")
        print(f"  Diff: {base}")
        print(f"  Old: {oldest.name}")
        print(f"  New: {newest.name}")
        print(f"{'─'*55}")
        try:
            result = subprocess.run(
                ["diff", "--color=always", "-u", str(oldest), str(newest)],
                capture_output=True, text=True
            )
            if result.stdout:
                # Limit output to avoid flooding terminal
                lines = result.stdout.splitlines()
                if len(lines) > 60:
                    print("\n".join(lines[:60]))
                    print(f"  ... ({len(lines) - 60} more lines, run diff manually for full output)")
                else:
                    print(result.stdout)
            else:
                print("  (no differences)")
        except FileNotFoundError:
            print("  diff command not found — install diffutils")

# ── List command ───────────────────────────────────────────────────────────────
def cmd_list(project_dir: Path | None = None):
    if project_dir is None:
        project_dir = Path.cwd()

    archive_dir = project_dir / ".claude" / "archive"
    if not archive_dir.exists():
        print(f"No archive at: {archive_dir}")
        return

    files = sorted(archive_dir.glob("*.md"))
    if not files:
        print("Archive is empty.")
        return

    print(f"\nArchive: {archive_dir}  ({len(files)} files)\n")
    for f in files:
        size = f.stat().st_size
        mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        phase = "pre " if f.stem.endswith("-pre") else "post"
        print(f"  [{phase}] {f.name:<55} {size:>6} B   {mtime}")
    print()

# ── Entry point ────────────────────────────────────────────────────────────────
def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"

    if cmd == "today":
        cmd_stats(filter_today=True)
    elif cmd == "diff":
        project_arg = Path(sys.argv[2]) if len(sys.argv) > 2 else None
        cmd_diff(project_arg)
    elif cmd == "list":
        project_arg = Path(sys.argv[2]) if len(sys.argv) > 2 else None
        cmd_list(project_arg)
    else:
        cmd_stats(filter_today=False)

if __name__ == "__main__":
    main()
