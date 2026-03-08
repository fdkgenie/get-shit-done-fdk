#!/usr/bin/env python3
"""
GSD Sonnet-Gateway — Generated File Archiver
Dual hook: PreToolUse (archive BEFORE overwrite) + PostToolUse (archive AFTER write).

Timeline for a Write event:
  PreToolUse  → copy OLD file (before Claude overwrites) → archive/name-TIMESTAMP-pre.md
  [Claude writes file]
  PostToolUse → copy NEW file (after Claude writes)      → archive/name-TIMESTAMP-post.md

Why both?
  - Pre:  preserve old version, never lose data even if Claude crashes mid-write
  - Post: save new version for diff/audit later

Watched files read from gsd-complexity-config.json (key "watched_files").
Fallback default: GSD planning files (.planning/**/*.md)

Auto-updates project .gitignore if entry for .claude/archive/ doesn't exist.

Setup:
  chmod +x ~/.claude/hooks/gsd-archive-files.py

Register in ~/.claude/settings.json:
  {
    "hooks": {
      "PreToolUse": [{
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [{"type": "command",
                   "command": "python3 \"$HOME/.claude/hooks/gsd-archive-files.py\" pre",
                   "timeout": 5}]
      }],
      "PostToolUse": [{
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [{"type": "command",
                   "command": "python3 \"$HOME/.claude/hooks/gsd-archive-files.py\" post",
                   "timeout": 5}]
      }]
    }
  }

Test manually:
  # Test Pre (archive old file before write)
  echo '{"tool_name":"Write","tool_input":{"file_path":"/your/project/.planning/STATE.md"}}' \\
    | CLAUDE_PROJECT_DIR="/your/project" python3 ~/.claude/hooks/gsd-archive-files.py pre

  # Test Post (archive new file after write)
  echo '{"tool_name":"Write","tool_input":{"file_path":"/your/project/.planning/STATE.md"}}' \\
    | CLAUDE_PROJECT_DIR="/your/project" python3 ~/.claude/hooks/gsd-archive-files.py post
"""
import sys
import json
import os
import shutil
import fnmatch
from datetime import datetime
from pathlib import Path

# ── Paths & defaults ───────────────────────────────────────────────────────────
CONFIG_PATH = Path.home() / ".claude" / "hooks" / "gsd-complexity-config.json"

DEFAULT_WATCHED = [
    ".planning/**/PLAN.md",
    ".planning/**/SUMMARY.md",
    ".planning/**/RESEARCH.md",
    ".planning/**/CONTEXT.md",
    ".planning/STATE.md",
    ".planning/ROADMAP.md",
    ".planning/REQUIREMENTS.md",
]

DEFAULT_GITIGNORE_ENTRIES = [
    ".claude/archive/",
    ".claude/logs/",
]

# ── Config loader ──────────────────────────────────────────────────────────────
def load_watched_patterns() -> list:
    """Load watched file patterns from config file."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                cfg = json.load(f)
            patterns = cfg.get("watched_files")
            if isinstance(patterns, list) and patterns:
                return patterns
        except (json.JSONDecodeError, OSError, KeyError) as e:
            # Log config load errors but don't fail - use defaults
            print(f"[gsd-archive] Warning: Could not load config from {CONFIG_PATH}: {e}", file=sys.stderr)
    return DEFAULT_WATCHED

def load_gitignore_entries() -> list:
    """Load gitignore entries from config file."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                cfg = json.load(f)
            entries = cfg.get("gitignore_entries")
            if isinstance(entries, list):
                return entries
        except (json.JSONDecodeError, OSError, KeyError) as e:
            # Log config load errors but don't fail - use defaults
            print(f"[gsd-archive] Warning: Could not load gitignore entries from {CONFIG_PATH}: {e}", file=sys.stderr)
    return DEFAULT_GITIGNORE_ENTRIES

# ── Project dir ────────────────────────────────────────────────────────────────
def get_project_dir() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())

# ── Pattern matcher ────────────────────────────────────────────────────────────
def should_watch(file_path: Path, project_dir: Path, patterns: list) -> bool:
    """Check if file matches any watch pattern."""
    try:
        relative_path = file_path.relative_to(project_dir)
        rel_str = str(relative_path)
        for pattern in patterns:
            if fnmatch.fnmatch(rel_str, pattern):
                return True
    except (ValueError, OSError) as e:
        # file_path is not relative to project_dir or path access error
        print(f"[gsd-archive] Warning: Could not check pattern for {file_path}: {e}", file=sys.stderr)
    return False

# ── Archiver ───────────────────────────────────────────────────────────────────
def archive_file(src: Path, archive_dir: Path, phase: str) -> str | None:
    """
    Copy src into archive_dir with timestamp + phase label suffix.
    phase: "pre" | "post"
    Returns archive path string or None if src doesn't exist.
    """
    if not src.exists():
        return None

    try:
        ts           = datetime.now().strftime("%Y%m%d-%H%M%S")
        archive_name = f"{src.stem}-{ts}-{phase}{src.suffix}"
        archive_path = archive_dir / archive_name

        archive_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, archive_path)
        return str(archive_path)
    except (OSError, shutil.Error) as e:
        print(f"[gsd-archive] Error: Could not archive {src}: {e}", file=sys.stderr)
        return None

# ── .gitignore updater ─────────────────────────────────────────────────────────
def ensure_gitignore(project_dir: Path):
    """
    Add entries to .gitignore if not present.
    Only runs once per project (check before write).
    """
    try:
        gitignore_path = project_dir / ".gitignore"
        entries_needed = load_gitignore_entries()

        existing_text = gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""
        existing_lines = set(existing_text.splitlines())

        missing = [e for e in entries_needed if e not in existing_lines]
        if not missing:
            return  # nothing to do

        block = "\n# GSD Sonnet-Gateway — auto-generated by archive hook\n" + "\n".join(missing) + "\n"
        with open(gitignore_path, "a", encoding="utf-8") as f:
            f.write(block)

        print(f"[gsd-archive] .gitignore updated: added {missing}", file=sys.stderr)
    except (OSError, UnicodeDecodeError) as e:
        # gitignore update failure doesn't block main flow
        print(f"[gsd-archive] Warning: Could not update .gitignore: {e}", file=sys.stderr)

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    # phase argument: "pre" | "post" (passed as argv[1])
    phase = sys.argv[1] if len(sys.argv) > 1 else "post"
    if phase not in ("pre", "post"):
        phase = "post"

    try:
        data       = json.loads(sys.stdin.read())
        tool_name  = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})

        # Only process Write and Edit tools
        if tool_name not in ("Write", "Edit", "MultiEdit"):
            sys.exit(0)

        # Get file path from tool input (Write uses "file_path", Edit uses "path")
        file_path = (
            tool_input.get("file_path")
            or tool_input.get("path")
            or ""
        )
        if not file_path:
            sys.exit(0)

        # Validate file path to prevent path traversal attacks
        try:
            written_path = Path(file_path).resolve()
        except (ValueError, OSError) as e:
            print(f"[gsd-archive] Error: Invalid file path: {e}", file=sys.stderr)
            sys.exit(1)

        project_dir = get_project_dir()

        # Ensure file path is within project directory (prevent path traversal)
        try:
            written_path.relative_to(project_dir)
        except ValueError:
            # File is outside project directory - potentially malicious
            print(f"[gsd-archive] Warning: File path outside project directory, skipping: {written_path}", file=sys.stderr)
            sys.exit(0)

        # Only archive if file matches watch patterns
        patterns = load_watched_patterns()
        if not should_watch(written_path, project_dir, patterns):
            sys.exit(0)

        archive_dir = project_dir / ".claude" / "archive"

        # Pre phase: archive OLD version (file exists before Claude writes)
        # Post phase: archive NEW version (file after Claude writes)
        # Both use same logic, just different phase label in filename
        archived = archive_file(written_path, archive_dir, phase)

        if archived:
            label = "pre-archive (old)" if phase == "pre" else "post-archive (new)"
            print(
                f"[gsd-archive/{label}] {written_path.name} → {Path(archived).name}",
                file=sys.stderr,
            )
        elif phase == "pre":
            # File doesn't exist yet (first write) — not an error
            print(
                f"[gsd-archive/pre] {written_path.name} not found (first write, skipping pre-archive)",
                file=sys.stderr,
            )

        # Ensure .gitignore has appropriate entries
        # Only run once in post phase to avoid double-check
        if phase == "post":
            ensure_gitignore(project_dir)

        sys.exit(0)

    except json.JSONDecodeError:
        print("gsd-sonnet-gate archiver: invalid JSON input", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"gsd-sonnet-gate archiver error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
